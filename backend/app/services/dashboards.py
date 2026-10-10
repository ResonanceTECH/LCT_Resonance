"""Dashboards and employer analytics. Calculated here; the frontend only renders them."""

from __future__ import annotations

from collections import Counter
from uuid import UUID

from sqlalchemy import ColumnElement, distinct, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.candidate import CandidateProfile, CandidateSkill
from app.models.company import Company
from app.models.engagement import Application, ProfileView, SavedVacancy, ShortlistItem
from app.models.enums import OfferStatus, Readiness, VacancyStatus
from app.models.offer import Offer
from app.models.taxonomy import Skill, Specialization
from app.models.user import User
from app.models.vacancy import Vacancy
from app.schemas.engagement import (
    CandidateDashboard,
    Conversion,
    EmployerAnalytics,
    EmployerDashboard,
    Funnel,
    ReadinessCount,
    SkillCount,
    SpecializationCount,
)
from app.services import matching, profiles
from app.services.candidate import get_profile
from app.services.notifications import unread_count

TOP_SKILLS = 8


async def _count(db: AsyncSession, model, *conditions: ColumnElement[bool]) -> int:
    result = await db.execute(select(func.count()).select_from(model).where(*conditions))
    return int(result.scalar_one())


async def candidate_dashboard(db: AsyncSession, user: User) -> CandidateDashboard:
    profile = await get_profile(db, user.id)
    facts = (await profiles.load_facts(db, [user.id]))[user.id]
    completeness = profiles.completeness(profile, facts)
    if facts.fsp_synced_at is not None:
        fsp_status = f"Синхронизировано {facts.fsp_synced_at:%d.%m.%Y}"
        if not facts.has_fsp:
            fsp_status += " · истории ФСП нет"
    else:
        fsp_status = "Нет синхронизации"
    return CandidateDashboard(
        profile_views=await _count(db, ProfileView, ProfileView.candidate_user_id == user.id),
        offers_received=await _count(db, Offer, Offer.candidate_user_id == user.id),
        offers_accepted=await _count(
            db,
            Offer,
            Offer.candidate_user_id == user.id,
            Offer.status == OfferStatus.accepted.value,
        ),
        profile_status="Заполнен" if completeness.percent >= 80 else "Требует внимания",
        fsp_sync_status=fsp_status,
        completeness=completeness,
        unread_notifications=await unread_count(db, user.id),
        saved_vacancies_count=await _count(
            db, SavedVacancy, SavedVacancy.candidate_user_id == user.id
        ),
        applications_count=await _count(db, Application, Application.candidate_user_id == user.id),
    )


def _open_candidates() -> list[ColumnElement[bool]]:
    return [
        *profiles.visible_to_employers(),
        CandidateProfile.readiness != Readiness.not_looking.value,
    ]


async def _open_candidates_count(db: AsyncSession) -> int:
    result = await db.execute(
        select(func.count())
        .select_from(CandidateProfile)
        .join(User, User.id == CandidateProfile.user_id)
        .where(*_open_candidates())
    )
    return int(result.scalar_one())


async def _offer_counts(db: AsyncSession, employer_id: UUID) -> Counter[str]:
    rows = await db.execute(
        select(Offer.status, func.count())
        .where(Offer.employer_user_id == employer_id)
        .group_by(Offer.status)
    )
    return Counter(dict(rows.all()))


async def employer_dashboard(db: AsyncSession, user: User) -> EmployerDashboard:
    offers = await _offer_counts(db, user.id)
    return EmployerDashboard(
        candidates_found=await _open_candidates_count(db),
        shortlist_size=await _count(db, ShortlistItem, ShortlistItem.employer_user_id == user.id),
        offers_sent=sum(offers.values()),
        offers_accepted=offers[OfferStatus.accepted.value],
        unread_notifications=await unread_count(db, user.id),
    )


async def _avg_match_score(db: AsyncSession, employer_id: UUID) -> int | None:
    """Average score of the category candidates for the employer's newest active vacancy."""
    vacancy = (
        await db.execute(
            select(Vacancy)
            .join(Company, Company.id == Vacancy.company_id)
            .where(
                Company.owner_user_id == employer_id, Vacancy.status == VacancyStatus.active.value
            )
            .options(*matching.VACANCY_OPTIONS)
            .order_by(Vacancy.created_at.desc())
            .limit(1)
        )
    ).scalar_one_or_none()
    if vacancy is None:
        return None
    candidates = (
        (
            await db.execute(
                select(CandidateProfile)
                .join(User, User.id == CandidateProfile.user_id)
                .where(
                    *_open_candidates(),
                    CandidateProfile.verified_specialization_id == vacancy.specialization_id,
                    CandidateProfile.verified_grade_id == vacancy.grade_id,
                )
                .options(*matching.MATCH_PROFILE_OPTIONS)
            )
        )
        .scalars()
        .all()
    )
    matches = await matching.match_profiles(vacancy, list(candidates))
    if not matches:
        return None
    return round(sum(m.score for m in matches.values()) / len(matches))


async def employer_analytics(db: AsyncSession, user: User) -> EmployerAnalytics:
    offers = await _offer_counts(db, user.id)
    sent = sum(offers.values())
    accepted = offers[OfferStatus.accepted.value]
    viewed = int(
        (
            await db.execute(
                select(func.count(distinct(ProfileView.candidate_user_id))).where(
                    ProfileView.employer_user_id == user.id
                )
            )
        ).scalar_one()
    )
    shortlisted = await _count(db, ShortlistItem, ShortlistItem.employer_user_id == user.id)

    pool = (
        select(CandidateProfile.user_id)
        .join(User, User.id == CandidateProfile.user_id)
        .where(*_open_candidates())
    )
    by_spec = await db.execute(
        select(Specialization.name, func.count())
        .join(CandidateProfile, CandidateProfile.declared_specialization_id == Specialization.id)
        .where(CandidateProfile.user_id.in_(pool))
        .group_by(Specialization.name)
        .order_by(func.count().desc())
    )
    readiness = await db.execute(
        select(CandidateProfile.readiness, func.count())
        .join(User, User.id == CandidateProfile.user_id)
        .where(*profiles.visible_to_employers())
        .group_by(CandidateProfile.readiness)
    )
    top_skills = await db.execute(
        select(Skill.name, func.count())
        .join(CandidateSkill, CandidateSkill.skill_id == Skill.id)
        .where(CandidateSkill.candidate_user_id.in_(pool))
        .group_by(Skill.name)
        .order_by(func.count().desc(), Skill.name)
        .limit(TOP_SKILLS)
    )
    return EmployerAnalytics(
        funnel=Funnel(
            viewed_candidates=viewed,
            shortlisted=shortlisted,
            offers_sent=sent,
            offers_accepted=accepted,
            offers_declined=offers[OfferStatus.declined.value],
        ),
        conversion=Conversion(
            shortlist_rate=shortlisted / viewed if viewed else 0.0,
            offer_accept_rate=accepted / sent if sent else 0.0,
        ),
        by_specialization=[
            SpecializationCount(specialization=n, count=c) for n, c in by_spec.all()
        ],
        avg_match_score=await _avg_match_score(db, user.id),
        readiness_breakdown=[ReadinessCount(readiness=r, count=c) for r, c in readiness.all()],
        top_skills=[SkillCount(skill=n, count=c) for n, c in top_skills.all()],
    )
