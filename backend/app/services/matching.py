from __future__ import annotations

from uuid import UUID

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import get_settings
from app.core.errors import AppError
from app.integrations.matching.baseline import BaselineMatcher, reasons_from_codes
from app.models.candidate import CandidateProfile, CandidateSkill
from app.models.enums import UserStatus, VacancyStatus
from app.models.fsp import FspAchievement
from app.models.taxonomy import Grade, Skill, Specialization
from app.models.user import User
from app.models.vacancy import Vacancy, VacancySkill
from app.schemas.matcher_contract import (
    MatcherCandidate,
    MatcherCandidateAchievement,
    MatcherNeed,
    MatchingRequest,
)
from app.schemas.matching import (
    MatchingCandidateCard,
    MatchingItem,
    MatchingNeed,
    MatchingSearchRequest,
    MatchingSearchResponse,
    NeedSkill,
)
from app.services.audit import write_audit


async def _resolve_need(
    db: AsyncSession, payload: MatchingSearchRequest
) -> tuple[MatchingNeed, dict[UUID, Skill]]:
    if payload.vacancy_id:
        vacancy = await db.get(Vacancy, payload.vacancy_id)
        if vacancy is None:
            raise AppError("VACANCY_NOT_FOUND", "Vacancy not found", 404)
        result = await db.execute(
            select(VacancySkill)
            .where(VacancySkill.vacancy_id == vacancy.id)
            .options(selectinload(VacancySkill.skill))
        )
        vskills = result.scalars().all()
        need = MatchingNeed(
            specialization_id=vacancy.specialization_id,
            grade_id=vacancy.grade_id,
            salary_from=vacancy.salary_from,
            salary_to=vacancy.salary_to,
            work_format=vacancy.work_format,
            skills=[NeedSkill(skill_id=vs.skill_id, required=vs.required) for vs in vskills],
        )
    elif payload.need:
        need = payload.need
    else:
        raise AppError("NEED_REQUIRED", "vacancy_id or need is required", 422)

    skill_ids = [s.skill_id for s in need.skills]
    skills_map: dict[UUID, Skill] = {}
    if skill_ids:
        rows = (
            await db.execute(select(Skill).where(Skill.id.in_(skill_ids)))
        ).scalars().all()
        skills_map = {s.id: s for s in rows}
    return need, skills_map


async def search_matches(
    db: AsyncSession, *, employer_id: UUID, payload: MatchingSearchRequest
) -> MatchingSearchResponse:
    need, skills_map = await _resolve_need(db, payload)
    spec = await db.get(Specialization, need.specialization_id)
    grade = await db.get(Grade, need.grade_id)
    if not spec or not grade:
        raise AppError("TAXONOMY_NOT_FOUND", "Invalid specialization/grade", 404)

    stmt = (
        select(CandidateProfile)
        .join(User, User.id == CandidateProfile.user_id)
        .where(
            User.status == UserStatus.active.value,
            CandidateProfile.open_to_offers.is_(True),
            CandidateProfile.verified_specialization_id == need.specialization_id,
            CandidateProfile.verified_grade_id == need.grade_id,
        )
        .options(selectinload(CandidateProfile.skills).selectinload(CandidateSkill.skill))
    )
    profiles = (await db.execute(stmt)).scalars().all()

    required_slugs = [
        skills_map[s.skill_id].slug for s in need.skills if s.required and s.skill_id in skills_map
    ]
    optional_slugs = [
        skills_map[s.skill_id].slug
        for s in need.skills
        if not s.required and s.skill_id in skills_map
    ]

    matcher_candidates: list[MatcherCandidate] = []
    profile_map: dict[str, CandidateProfile] = {}
    for p in profiles:
        if need.salary_to is not None and p.salary_min is not None and p.salary_min > need.salary_to:
            continue
        ach_rows = (
            await db.execute(
                select(FspAchievement).where(FspAchievement.candidate_user_id == p.user_id)
            )
        ).scalars().all()
        matcher_candidates.append(
            MatcherCandidate(
                id=str(p.user_id),
                verified_specialization=spec.slug,
                verified_grade=grade.code,
                test_score=p.last_test_score,
                skills=[cs.skill.slug for cs in p.skills if cs.skill],
                fsp_achievements=[
                    MatcherCandidateAchievement(
                        type=a.achievement_type,
                        discipline=a.discipline,
                        result=a.result,
                    )
                    for a in ach_rows
                ],
                salary_min=p.salary_min,
                work_format=p.work_format,
            )
        )
        profile_map[str(p.user_id)] = p

    request = MatchingRequest(
        need=MatcherNeed(
            specialization=spec.slug,
            grade=grade.code,
            required_skills=required_slugs,
            optional_skills=optional_slugs,
            salary_to=need.salary_to,
            work_format=need.work_format,
        ),
        candidates=matcher_candidates,
    )

    matcher_name = "baseline"
    response = None
    settings = get_settings()
    if settings.matcher_provider == "ml" and settings.ml_matcher_url:
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                resp = await client.post(
                    f"{settings.ml_matcher_url.rstrip('/')}/rank",
                    json=request.model_dump(),
                )
            resp.raise_for_status()
            from app.schemas.matcher_contract import MatchingResponse as MR

            response = MR.model_validate(resp.json())
            matcher_name = "ml"
        except Exception:
            response = None

    if response is None:
        response = await BaselineMatcher().rank(request)
        matcher_name = "baseline"

    items: list[MatchingItem] = []
    for m in response.matches:
        p = profile_map.get(m.candidate_id)
        if not p:
            continue
        first = p.first_name or ""
        last = (p.last_name or "")[:1]
        display = f"{first} {last}.".strip() if last else (first or "Candidate")
        from app.schemas.common import MatchDTO

        items.append(
            MatchingItem(
                candidate=MatchingCandidateCard(
                    id=p.user_id,
                    display_name=display,
                    specialization=spec.name,
                    grade=grade.name,
                    skills=[cs.skill.name for cs in p.skills if cs.skill],
                    has_fsp_history=bool(m.components.fsp > 0),
                ),
                match=MatchDTO(
                    score=m.score,
                    components=m.components,
                    matched_skills=m.matched_skills,
                    missing_skills=m.missing_skills,
                    reasons=reasons_from_codes(m.reason_codes, p.last_test_score),
                ),
            )
        )

    total = len(items)
    sliced = items[payload.offset : payload.offset + payload.limit]
    await write_audit(
        db,
        action="MATCH_REQUESTED",
        entity_type="matching",
        entity_id=str(employer_id),
        actor_user_id=employer_id,
        metadata={"total": total, "matcher": matcher_name},
    )
    await db.commit()
    return MatchingSearchResponse(
        items=sliced,
        total=total,
        limit=payload.limit,
        offset=payload.offset,
        matcher=matcher_name,
    )
