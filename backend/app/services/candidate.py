from __future__ import annotations

from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.errors import AppError
from app.models.candidate import CandidateProfile, CandidateSkill
from app.models.enums import UserStatus
from app.models.fsp import FspAchievement
from app.models.taxonomy import Grade, Skill, Specialization
from app.models.user import User
from app.schemas.candidate import (
    CandidateMeResponse,
    CandidatePublicResponse,
    CandidateSkillIn,
    CandidateUpdate,
)
from app.schemas.common import IdName, Page


async def _id_name_spec(db: AsyncSession, spec_id: UUID | None) -> IdName | None:
    if not spec_id:
        return None
    row = await db.get(Specialization, spec_id)
    return IdName(id=str(row.id), name=row.name) if row else None


async def _id_name_grade(db: AsyncSession, grade_id: UUID | None) -> IdName | None:
    if not grade_id:
        return None
    row = await db.get(Grade, grade_id)
    return IdName(id=str(row.id), name=row.name) if row else None


async def get_profile(db: AsyncSession, user_id: UUID) -> CandidateProfile:
    result = await db.execute(
        select(CandidateProfile)
        .where(CandidateProfile.user_id == user_id)
        .options(selectinload(CandidateProfile.skills).selectinload(CandidateSkill.skill))
    )
    profile = result.scalar_one_or_none()
    if profile is None:
        raise AppError("PROFILE_NOT_FOUND", "Candidate profile not found", 404)
    return profile


async def has_fsp(db: AsyncSession, user_id: UUID) -> bool:
    result = await db.execute(
        select(func.count())
        .select_from(FspAchievement)
        .where(FspAchievement.candidate_user_id == user_id)
    )
    return int(result.scalar_one()) > 0


async def to_me_response(db: AsyncSession, profile: CandidateProfile) -> CandidateMeResponse:
    skill_names = [cs.skill.name for cs in profile.skills if cs.skill]
    return CandidateMeResponse(
        id=profile.user_id,
        first_name=profile.first_name,
        last_name=profile.last_name,
        phone=profile.phone,
        telegram=profile.telegram,
        city=profile.city,
        bio=profile.bio,
        experience_months=profile.experience_months,
        declared_specialization=await _id_name_spec(db, profile.declared_specialization_id),
        declared_grade=await _id_name_grade(db, profile.declared_grade_id),
        verified_specialization=await _id_name_spec(db, profile.verified_specialization_id),
        verified_grade=await _id_name_grade(db, profile.verified_grade_id),
        grade_verification_status=profile.grade_verification_status,
        salary_min=profile.salary_min,
        work_format=profile.work_format,
        open_to_offers=profile.open_to_offers,
        skills=skill_names,
        has_fsp_history=await has_fsp(db, profile.user_id),
        last_test_score=profile.last_test_score,
    )


async def to_public_response(
    db: AsyncSession, profile: CandidateProfile
) -> CandidatePublicResponse:
    skill_names = [cs.skill.name for cs in profile.skills if cs.skill]
    first = profile.first_name or ""
    last = (profile.last_name or "")[:1]
    display = f"{first} {last}.".strip() if last else (first or "Candidate")
    verified_spec = await _id_name_spec(db, profile.verified_specialization_id)
    verified_grade = await _id_name_grade(db, profile.verified_grade_id)
    return CandidatePublicResponse(
        id=profile.user_id,
        display_name=display,
        city=profile.city,
        bio=profile.bio,
        experience_months=profile.experience_months,
        specialization=verified_spec.name if verified_spec else None,
        grade=verified_grade.name if verified_grade else None,
        skills=skill_names,
        salary_min=profile.salary_min,
        work_format=profile.work_format,
        open_to_offers=profile.open_to_offers,
        has_fsp_history=await has_fsp(db, profile.user_id),
        last_test_score=profile.last_test_score,
    )


async def update_profile(
    db: AsyncSession, user_id: UUID, payload: CandidateUpdate
) -> CandidateMeResponse:
    profile = await get_profile(db, user_id)
    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(profile, key, value)
    await db.commit()
    profile = await get_profile(db, user_id)
    return await to_me_response(db, profile)


async def replace_skills(
    db: AsyncSession, user_id: UUID, skills: list[CandidateSkillIn]
) -> CandidateMeResponse:
    await get_profile(db, user_id)
    await db.execute(delete(CandidateSkill).where(CandidateSkill.candidate_user_id == user_id))
    for item in skills:
        skill = await db.get(Skill, item.skill_id)
        if skill is None:
            raise AppError("SKILL_NOT_FOUND", f"Skill {item.skill_id} not found", 404)
        db.add(
            CandidateSkill(
                candidate_user_id=user_id,
                skill_id=item.skill_id,
                level=item.level,
            )
        )
    await db.commit()
    profile = await get_profile(db, user_id)
    return await to_me_response(db, profile)


async def list_candidates(
    db: AsyncSession,
    *,
    specialization_id: UUID | None,
    grade_id: UUID | None,
    open_to_offers: bool | None,
    limit: int,
    offset: int,
) -> Page[CandidatePublicResponse]:
    stmt = (
        select(CandidateProfile)
        .join(User, User.id == CandidateProfile.user_id)
        .where(User.status == UserStatus.active.value)
        .options(selectinload(CandidateProfile.skills).selectinload(CandidateSkill.skill))
    )
    if specialization_id:
        stmt = stmt.where(CandidateProfile.verified_specialization_id == specialization_id)
    if grade_id:
        stmt = stmt.where(CandidateProfile.verified_grade_id == grade_id)
    if open_to_offers is not None:
        stmt = stmt.where(CandidateProfile.open_to_offers.is_(open_to_offers))

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = int((await db.execute(count_stmt)).scalar_one())
    rows = (
        await db.execute(stmt.order_by(CandidateProfile.updated_at.desc()).limit(limit).offset(offset))
    ).scalars().all()
    items = [await to_public_response(db, p) for p in rows]
    return Page(items=items, total=total, limit=limit, offset=offset)
