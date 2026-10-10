"""Candidate profile -> frontend `CandidateProfile`, loaded in batches (no N+1)."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from sqlalchemy import ColumnElement, select
from sqlalchemy.dialects.postgresql import distinct_on
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.candidate import CandidateProfile, CandidateSkill
from app.models.enums import ProfileVisibility, TestAttemptStatus, UserRole, UserStatus
from app.models.fsp import FspAchievement, FspLink
from app.models.testing import TestAttempt
from app.models.user import User
from app.schemas.candidate import (
    CandidateMeOut,
    CandidateProfileOut,
    ProfileCompleteness,
    ProfileCompletenessItem,
    TestResultSummary,
)

PROFILE_OPTIONS = (
    selectinload(CandidateProfile.skills).selectinload(CandidateSkill.skill),
    selectinload(CandidateProfile.declared_specialization),
    selectinload(CandidateProfile.declared_grade),
    selectinload(CandidateProfile.verified_specialization),
    selectinload(CandidateProfile.verified_grade),
)
VISIBLE_PROFILE_VALUES = (ProfileVisibility.employers.value, ProfileVisibility.public.value)
DEFAULT_GRADE = "junior"


def visible_to_employers() -> list[ColumnElement[bool]]:
    """Candidates employers may see (unverified email or hidden profile: not shown).
    The query must join `User`."""
    return [
        User.role == UserRole.candidate.value,
        User.status == UserStatus.active.value,
        User.email_verified_at.is_not(None),
        CandidateProfile.profile_visibility.in_(VISIBLE_PROFILE_VALUES),
    ]


@dataclass(frozen=True)
class ProfileFacts:
    """Computed parts of the profile that live in other tables."""

    test_result: TestResultSummary | None = None
    fsp_synced_at: datetime | None = None
    has_fsp: bool = False


async def load_facts(db: AsyncSession, user_ids: Iterable[UUID]) -> dict[UUID, ProfileFacts]:
    ids = list(user_ids)
    if not ids:
        return {}
    latest_tests = await db.execute(
        select(TestAttempt)
        .where(
            TestAttempt.candidate_user_id.in_(ids),
            TestAttempt.status == TestAttemptStatus.completed.value,
        )
        .order_by(TestAttempt.candidate_user_id, TestAttempt.submitted_at.desc())
        .ext(distinct_on(TestAttempt.candidate_user_id))  # latest attempt per candidate
    )
    tests = {
        a.candidate_user_id: TestResultSummary(
            score=a.score or 0,
            grade_confirmed=bool(a.passed),
            completed_at=a.submitted_at or a.created_at,
        )
        for a in latest_tests.scalars().all()
    }
    synced = dict(
        (
            await db.execute(
                select(FspLink.candidate_user_id, FspLink.last_synced_at).where(
                    FspLink.candidate_user_id.in_(ids)
                )
            )
        ).all()
    )
    with_fsp = set(
        (
            await db.execute(
                select(FspAchievement.candidate_user_id)
                .where(FspAchievement.candidate_user_id.in_(ids), FspAchievement.verified.is_(True))
                .distinct()
            )
        ).scalars()
    )
    return {uid: ProfileFacts(tests.get(uid), synced.get(uid), uid in with_fsp) for uid in ids}


def skill_names(profile: CandidateProfile) -> list[str]:
    return [cs.skill.name for cs in profile.skills if cs.skill]


def specialization_name(profile: CandidateProfile) -> str:
    spec = profile.declared_specialization or profile.verified_specialization
    return spec.name if spec else ""


def confirmed_grade(profile: CandidateProfile) -> str | None:
    return profile.verified_grade.code if profile.verified_grade else None


def completeness(profile: CandidateProfile, facts: ProfileFacts) -> ProfileCompleteness:
    """Backend-owned checklist; weights and links match the frontend screens."""
    edit = "/candidate/profile/edit"
    checks = [
        ("about", "О себе", len(profile.about or "") >= 20, 10, edit),
        ("skills", "Навыки (минимум 3)", len(profile.skills) >= 3, 15, edit),
        (
            "salary",
            "Зарплатные ожидания",
            bool(profile.salary_from and profile.salary_to),
            10,
            edit,
        ),
        ("city", "Город", bool(profile.city), 5, edit),
        ("format", "Формат работы", bool(profile.work_format), 10, edit),
        ("position", "Желаемая должность", bool(profile.desired_position), 10, edit),
        (
            "experience",
            "Опыт",
            profile.experience_years is not None or bool(profile.experience_description),
            10,
            edit,
        ),
        ("fsp", "Синхронизация ФСП", facts.fsp_synced_at is not None, 15, "/candidate/fsp"),
        ("test", "Профессиональный тест", facts.test_result is not None, 15, "/candidate/testing"),
    ]
    items = [
        ProfileCompletenessItem(key=key, label=label, done=done, weight=weight, href=href)
        for key, label, done, weight, href in checks
    ]
    total = sum(i.weight for i in items)
    earned = sum(i.weight for i in items if i.done)
    return ProfileCompleteness(percent=round(100 * earned / total), items=items)


def _fields(profile: CandidateProfile, facts: ProfileFacts) -> dict:
    return {
        "id": profile.user_id,
        "user_id": profile.user_id,
        "full_name": profile.full_name,
        "about": profile.about,
        "specialization": specialization_name(profile),
        "claimed_grade": profile.declared_grade.code if profile.declared_grade else DEFAULT_GRADE,
        "confirmed_grade": confirmed_grade(profile),
        "experience_years": profile.experience_years,
        "experience_description": profile.experience_description,
        "skills": skill_names(profile),
        "desired_position": profile.desired_position,
        "salary_from": profile.salary_from,
        "salary_to": profile.salary_to,
        "currency": profile.currency,
        "city": profile.city,
        "work_format": profile.work_format,
        "readiness": profile.readiness,
        "test_result": facts.test_result,
        "fsp_synced_at": facts.fsp_synced_at,
        "has_fsp_achievements": facts.has_fsp,
        "profile_completeness": completeness(profile, facts).percent,
    }


def to_out(profile: CandidateProfile, facts: ProfileFacts) -> CandidateProfileOut:
    return CandidateProfileOut(**_fields(profile, facts))


def to_me_out(profile: CandidateProfile, facts: ProfileFacts, user: User) -> CandidateMeOut:
    return CandidateMeOut(
        **_fields(profile, facts),
        phone=profile.phone,
        telegram=profile.telegram,
        email_verified=user.email_verified_at is not None,
    )


async def build_outs(
    db: AsyncSession, profiles: Sequence[CandidateProfile]
) -> list[CandidateProfileOut]:
    facts = await load_facts(db, (p.user_id for p in profiles))
    return [to_out(p, facts[p.user_id]) for p in profiles]
