"""GET /candidates — the employer's Talent Pool (Backend.md, "Query Talent Pool")."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import ColumnElement, Select, distinct, exists, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.candidate import CandidateProfile, CandidateSkill
from app.models.enums import Readiness
from app.models.fsp import FspAchievement
from app.models.taxonomy import Grade, Skill, Specialization
from app.models.user import User
from app.models.vacancy import Vacancy
from app.schemas.candidate import TalentPoolItem, TalentPoolResponse
from app.services import matching, profiles, taxonomy, vacancies

MAX_LIMIT = 50


@dataclass(frozen=True)
class TalentPoolQuery:
    specialization: str | None = None
    grade: str | None = None
    skills: str | None = None  # comma separated; the candidate must list all of them
    work_format: str | None = None
    salary_from: int | None = None
    salary_to: int | None = None
    fsp_discipline: str | None = None
    has_fsp_achievements: bool | None = None
    readiness: str | None = None
    vacancy_id: UUID | None = None
    q: str | None = None
    sort: str | None = None  # match | grade | salary | name
    page: int = 1
    limit: int = 20


def _fsp_exists(*conditions: ColumnElement[bool]) -> ColumnElement[bool]:
    return exists().where(
        FspAchievement.candidate_user_id == CandidateProfile.user_id,
        FspAchievement.verified.is_(True),
        *conditions,
    )


async def _conditions(db: AsyncSession, query: TalentPoolQuery) -> list[ColumnElement[bool]] | None:
    """SQL filters; None when a filter can match nobody (e.g. an unknown skill)."""
    conditions = profiles.visible_to_employers()
    if query.specialization:
        spec = await taxonomy.specialization_by_name(db, query.specialization)
        conditions.append(CandidateProfile.declared_specialization_id == spec.id)
    if query.grade:
        # Search is built on the category confirmed by testing, not on the declared one.
        grade = await taxonomy.grade_by_code(db, query.grade)
        conditions.append(CandidateProfile.verified_grade_id == grade.id)
    if query.work_format:
        conditions.append(CandidateProfile.work_format == query.work_format)
    if query.readiness:
        conditions.append(CandidateProfile.readiness == query.readiness)
    # Salary filters intersect the candidate's expectations with the requested range.
    if query.salary_from:
        conditions.append(
            or_(
                CandidateProfile.salary_to.is_(None),
                CandidateProfile.salary_to >= query.salary_from,
            )
        )
    if query.salary_to:
        conditions.append(
            or_(
                CandidateProfile.salary_from.is_(None),
                CandidateProfile.salary_from <= query.salary_to,
            )
        )
    if query.skills:
        wanted = await taxonomy.find_skills(db, query.skills.split(","))
        if wanted is None:
            return None
        if wanted:
            ids = {s.id for s in wanted}
            with_all = (
                select(CandidateSkill.candidate_user_id)
                .where(CandidateSkill.skill_id.in_(ids))
                .group_by(CandidateSkill.candidate_user_id)
                .having(func.count(distinct(CandidateSkill.skill_id)) == len(ids))
            )
            conditions.append(CandidateProfile.user_id.in_(with_all))
    if query.fsp_discipline:
        pattern = taxonomy.like_pattern(query.fsp_discipline)
        conditions.append(_fsp_exists(FspAchievement.discipline.ilike(pattern, escape="\\")))
    if query.has_fsp_achievements is not None:
        conditions.append(_fsp_exists() if query.has_fsp_achievements else ~_fsp_exists())
    if query.q:
        pattern = taxonomy.like_pattern(query.q)
        conditions.append(
            or_(
                CandidateProfile.full_name.ilike(pattern, escape="\\"),
                CandidateProfile.desired_position.ilike(pattern, escape="\\"),
                exists().where(
                    Specialization.id == CandidateProfile.declared_specialization_id,
                    Specialization.name.ilike(pattern, escape="\\"),
                ),
                exists().where(
                    CandidateSkill.candidate_user_id == CandidateProfile.user_id,
                    Skill.id == CandidateSkill.skill_id,
                    Skill.name.ilike(pattern, escape="\\"),
                ),
            )
        )
    return conditions


def _vacancy_gate(vacancy: Vacancy) -> list[ColumnElement[bool]]:
    """Hard filters for matching under a vacancy: tested into exactly its category."""
    return [
        CandidateProfile.verified_specialization_id == vacancy.specialization_id,
        CandidateProfile.verified_grade_id == vacancy.grade_id,
        CandidateProfile.readiness != Readiness.not_looking.value,
    ]


def _sorted(stmt: Select, sort: str | None) -> Select:
    if sort == "name":
        return stmt.order_by(CandidateProfile.full_name, CandidateProfile.user_id)
    if sort == "salary":
        return stmt.order_by(
            CandidateProfile.salary_to.desc().nulls_last(), CandidateProfile.user_id
        )
    if sort == "grade":
        return stmt.outerjoin(Grade, Grade.id == CandidateProfile.verified_grade_id).order_by(
            Grade.rank.desc().nulls_last(), CandidateProfile.user_id
        )
    return stmt.order_by(CandidateProfile.updated_at.desc(), CandidateProfile.user_id)


async def search(db: AsyncSession, query: TalentPoolQuery, *, viewer: User) -> TalentPoolResponse:
    conditions = await _conditions(db, query)
    if conditions is None:
        return TalentPoolResponse(items=[], total=0)
    limit = max(1, min(query.limit, MAX_LIMIT))
    offset = (max(query.page, 1) - 1) * limit
    base = (
        select(CandidateProfile).join(User, User.id == CandidateProfile.user_id).where(*conditions)
    )

    if query.vacancy_id is None:
        total = (await db.execute(select(func.count()).select_from(base.subquery()))).scalar_one()
        page = list(
            (
                await db.execute(
                    _sorted(base, query.sort)
                    .options(*profiles.PROFILE_OPTIONS)
                    .limit(limit)
                    .offset(offset)
                )
            ).scalars()
        )
        return TalentPoolResponse(
            items=[TalentPoolItem(**p.model_dump()) for p in await profiles.build_outs(db, page)],
            total=total,
        )

    # Under a vacancy: every candidate of its category is scored, then the page is cut.
    vacancy = await vacancies.get_editable(db, query.vacancy_id, viewer)
    candidates = list(
        (
            await db.execute(
                base.where(*_vacancy_gate(vacancy)).options(*matching.MATCH_PROFILE_OPTIONS)
            )
        ).scalars()
    )
    matches = await matching.match_profiles(vacancy, candidates)
    by_id = {p.user_id: p for p in candidates}
    if query.sort in (None, "", "match"):
        ranked = [by_id[cid] for cid in matches]  # matcher order
    else:
        order = [
            p.user_id
            for p in (
                await db.execute(_sorted(base.where(*_vacancy_gate(vacancy)), query.sort))
            ).scalars()
        ]
        ranked = [by_id[cid] for cid in order if cid in by_id]
    page = ranked[offset : offset + limit]
    outs = await profiles.build_outs(db, page)
    return TalentPoolResponse(
        items=[TalentPoolItem(**out.model_dump(), match=matches.get(out.id)) for out in outs],
        total=len(ranked),
    )
