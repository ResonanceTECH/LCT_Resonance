from __future__ import annotations

from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.candidate import CandidateProfile
from app.models.engagement import ShortlistItem
from app.models.user import User
from app.schemas.candidate import CandidateProfileOut
from app.services import profiles
from app.services.candidate import get_visible_profile


async def list_shortlist(db: AsyncSession, employer: User) -> list[CandidateProfileOut]:
    rows = await db.execute(
        select(CandidateProfile)
        .join(ShortlistItem, ShortlistItem.candidate_user_id == CandidateProfile.user_id)
        .join(User, User.id == CandidateProfile.user_id)
        .where(ShortlistItem.employer_user_id == employer.id, *profiles.visible_to_employers())
        .options(*profiles.PROFILE_OPTIONS)
        .order_by(ShortlistItem.created_at.desc())
    )
    return await profiles.build_outs(db, list(rows.scalars().all()))


async def add(db: AsyncSession, employer: User, candidate_id: UUID) -> None:
    await get_visible_profile(db, candidate_id)
    existing = await db.execute(
        select(ShortlistItem.id).where(
            ShortlistItem.employer_user_id == employer.id,
            ShortlistItem.candidate_user_id == candidate_id,
        )
    )
    if existing.first() is not None:
        return
    db.add(ShortlistItem(employer_user_id=employer.id, candidate_user_id=candidate_id))
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()  # added concurrently: the result is the same


async def remove(db: AsyncSession, employer: User, candidate_id: UUID) -> None:
    await db.execute(
        delete(ShortlistItem).where(
            ShortlistItem.employer_user_id == employer.id,
            ShortlistItem.candidate_user_id == candidate_id,
        )
    )
    await db.commit()
