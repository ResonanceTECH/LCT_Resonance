from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError
from app.models.candidate import CandidateProfile, CandidateSkill
from app.models.engagement import ProfileView
from app.models.enums import ConsentType, ProfileVisibility, UserRole, UserStatus
from app.models.user import User
from app.schemas.candidate import (
    CandidateMeOut,
    CandidateProfileOut,
    CandidateUpdate,
    ProfileCompleteness,
)
from app.schemas.consent import ConsentOut, ConsentsUpdate
from app.services import consents, profiles, taxonomy
from app.services.audit import write_audit
from app.services.fsp import drop_fsp_data


async def get_profile(db: AsyncSession, user_id: UUID) -> CandidateProfile:
    result = await db.execute(
        select(CandidateProfile)
        .where(CandidateProfile.user_id == user_id)
        .options(*profiles.PROFILE_OPTIONS)
    )
    profile = result.scalar_one_or_none()
    if profile is None:
        raise AppError("PROFILE_NOT_FOUND", "Профиль не найден", 404)
    return profile


async def get_visible_profile(db: AsyncSession, candidate_id: UUID) -> CandidateProfile:
    """A profile as employers may see it; hidden or inactive ones are a 404."""
    result = await db.execute(
        select(CandidateProfile)
        .join(User, User.id == CandidateProfile.user_id)
        .where(CandidateProfile.user_id == candidate_id, *profiles.visible_to_employers())
        .options(*profiles.PROFILE_OPTIONS)
    )
    profile = result.scalar_one_or_none()
    if profile is None:
        raise AppError("CANDIDATE_NOT_FOUND", "Кандидат не найден", 404)
    return profile


async def get_me(db: AsyncSession, user: User) -> CandidateMeOut:
    profile = await get_profile(db, user.id)
    facts = (await profiles.load_facts(db, [user.id]))[user.id]
    return profiles.to_me_out(profile, facts, user)


async def get_completeness(db: AsyncSession, user_id: UUID) -> ProfileCompleteness:
    profile = await get_profile(db, user_id)
    facts = (await profiles.load_facts(db, [user_id]))[user_id]
    return profiles.completeness(profile, facts)


async def update_me(db: AsyncSession, user: User, payload: CandidateUpdate) -> CandidateMeOut:
    profile = await get_profile(db, user.id)
    data = payload.model_dump(
        exclude_unset=True, exclude={"specialization", "claimed_grade", "skills"}
    )
    # A salary can be changed from one side only; the range must stay consistent.
    salary_from = data.get("salary_from", profile.salary_from)
    salary_to = data.get("salary_to", profile.salary_to)
    if salary_from and salary_to and salary_to < salary_from:
        raise AppError("INVALID_SALARY_RANGE", "Верхняя граница зарплаты меньше нижней", 422)

    if payload.specialization is not None:
        spec = await taxonomy.specialization_by_name(db, payload.specialization)
        profile.declared_specialization_id = spec.id
    if payload.claimed_grade is not None:
        profile.declared_grade_id = (await taxonomy.grade_by_code(db, payload.claimed_grade)).id
    if payload.skills is not None:
        skills = await taxonomy.resolve_skills(db, payload.skills)
        profile.skills.clear()
        # Delete old rows first: re-adding a kept skill must not hit uq_candidate_skill.
        await db.flush()
        profile.skills.extend(CandidateSkill(skill=skill) for skill in skills)
    for key, value in data.items():
        setattr(profile, key, value)
    if payload.full_name:
        user.display_name = payload.full_name
    await db.commit()
    # Relationships follow the new foreign keys only after a reload.
    db.expire(profile, ["declared_specialization", "declared_grade"])
    return await get_me(db, user)


async def get_for_employer(
    db: AsyncSession, candidate_id: UUID, viewer: User
) -> CandidateProfileOut:
    profile = await get_visible_profile(db, candidate_id)
    if viewer.role == UserRole.employer.value:
        # Counted for the candidate's dashboard ("profile views").
        db.add(ProfileView(candidate_user_id=candidate_id, employer_user_id=viewer.id))
        await db.commit()
    facts = (await profiles.load_facts(db, [candidate_id]))[candidate_id]
    return profiles.to_out(profile, facts)


async def get_consents(db: AsyncSession, user_id: UUID) -> list[ConsentOut]:
    return consents.to_out(await consents.latest_consents(db, user_id))


async def update_consents(
    db: AsyncSession, user_id: UUID, payload: ConsentsUpdate
) -> list[ConsentOut]:
    """Store consent changes and apply what they mean for the profile."""
    profile = await get_profile(db, user_id)
    await consents.apply_changes(db, user_id, payload.consents)
    # Effects follow the requested state, so "do not publish" works even if the consent
    # was never given before.
    requested = {ConsentType(c.type): c.accepted for c in payload.consents}
    if ConsentType.profile_publication in requested:
        profile.profile_visibility = (
            ProfileVisibility.employers.value
            if requested[ConsentType.profile_publication]
            else ProfileVisibility.private.value
        )
    if requested.get(ConsentType.fsp_sync) is False:
        # Withdrawn consent to FSP processing: stop using the data, not just stop syncing.
        await drop_fsp_data(db, user_id)
    await db.commit()
    return await get_consents(db, user_id)


async def delete_account(db: AsyncSession, user: User) -> None:
    """Soft delete: the account can no longer log in and disappears from search."""
    user.status = UserStatus.deleted.value
    await write_audit(
        db, action="USER_DELETED", entity_type="user", entity_id=str(user.id), actor_user_id=user.id
    )
    await db.commit()
