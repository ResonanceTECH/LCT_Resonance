from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.errors import AppError
from app.integrations.fsp import get_fsp_adapter
from app.integrations.fsp.mock import MockFSPTimeoutError
from app.models.enums import FspSyncStatus
from app.models.fsp import FspAchievement, FspLink
from app.schemas.fsp import FspAchievementOut, FspSyncResponse
from app.services.audit import write_audit


async def link_fsp(db: AsyncSession, *, user_id: UUID, fsp_member_id: str) -> FspLink:
    existing = await db.execute(
        select(FspLink).where(FspLink.fsp_member_id == fsp_member_id)
    )
    other = existing.scalar_one_or_none()
    if other and other.candidate_user_id != user_id:
        raise AppError("FSP_ID_ALREADY_LINKED", "FSP ID already linked to another account", 409)

    link = await db.get(FspLink, user_id)
    if link is None:
        link = FspLink(candidate_user_id=user_id, fsp_member_id=fsp_member_id)
        db.add(link)
    else:
        link.fsp_member_id = fsp_member_id
    await write_audit(
        db,
        action="FSP_LINKED",
        entity_type="fsp_link",
        entity_id=str(user_id),
        actor_user_id=user_id,
        metadata={"fsp_member_id": fsp_member_id},
    )
    await db.commit()
    await db.refresh(link)
    return link


async def unlink_fsp(db: AsyncSession, *, user_id: UUID) -> None:
    link = await db.get(FspLink, user_id)
    if link:
        await db.delete(link)
        await db.commit()


async def _achievements_out(db: AsyncSession, user_id: UUID) -> list[FspAchievementOut]:
    result = await db.execute(
        select(FspAchievement).where(FspAchievement.candidate_user_id == user_id)
    )
    rows = result.scalars().all()
    return [
        FspAchievementOut(
            id=a.id,
            type=a.achievement_type,
            competition_name=a.competition_name,
            discipline=a.discipline,
            place=a.place,
            result=a.result,
            role=a.role,
            sport_rank=a.sport_rank,
            verified=a.verified,
        )
        for a in rows
    ]


async def sync_fsp(db: AsyncSession, *, user_id: UUID) -> FspSyncResponse:
    settings = get_settings()
    link = await db.get(FspLink, user_id)
    if link is None:
        raise AppError("FSP_NOT_LINKED", "Link FSP ID first", 409)

    adapter = get_fsp_adapter()
    provider = settings.fsp_provider

    try:
        member = await asyncio.wait_for(
            adapter.get_member(link.fsp_member_id), timeout=settings.fsp_timeout_sec
        )
        achievements = await asyncio.wait_for(
            adapter.get_achievements(link.fsp_member_id), timeout=settings.fsp_timeout_sec
        )
    except (TimeoutError, MockFSPTimeoutError, Exception):
        # cache fallback
        if link.raw_snapshot is not None:
            link.sync_status = FspSyncStatus.stale.value
            await db.commit()
            items = await _achievements_out(db, user_id)
            return FspSyncResponse(
                status="stale",
                provider=provider,
                fsp_member_id=link.fsp_member_id,
                last_synced_at=link.last_synced_at,
                is_stale=True,
                achievements_count=len(items),
                achievements=items,
            )
        raise AppError("FSP_UNAVAILABLE", "FSP provider unavailable", 503)

    if not member.exists:
        link.sync_status = FspSyncStatus.no_history.value
        link.last_synced_at = datetime.now(UTC)
        link.raw_snapshot = {"member": member.model_dump(), "achievements": []}
        await db.commit()
        return FspSyncResponse(
            status="no_history",
            provider=provider,
            fsp_member_id=link.fsp_member_id,
            last_synced_at=link.last_synced_at,
            achievements_count=0,
            achievements=[],
        )

    # upsert achievements
    for dto in achievements:
        result = await db.execute(
            select(FspAchievement).where(
                FspAchievement.candidate_user_id == user_id,
                FspAchievement.source == "fsp",
                FspAchievement.external_id == dto.external_id,
            )
        )
        row = result.scalar_one_or_none()
        if row is None:
            row = FspAchievement(
                candidate_user_id=user_id,
                source="fsp",
                external_id=dto.external_id,
            )
            db.add(row)
        row.achievement_type = dto.achievement_type
        row.discipline = dto.discipline
        row.competition_name = dto.competition_name
        row.result = dto.result
        row.place = dto.place
        row.role = dto.role
        row.sport_rank = dto.sport_rank
        row.achieved_at = dto.achieved_at
        row.verified = True

    status = FspSyncStatus.synced.value if achievements else FspSyncStatus.no_history.value
    link.sync_status = status
    link.last_synced_at = datetime.now(UTC)
    link.raw_snapshot = {
        "member": member.model_dump(mode="json"),
        "achievements": [a.model_dump(mode="json") for a in achievements],
    }
    await write_audit(
        db,
        action="FSP_SYNCED",
        entity_type="fsp_link",
        entity_id=str(user_id),
        actor_user_id=user_id,
        metadata={"status": status, "count": len(achievements)},
    )
    await db.commit()
    items = await _achievements_out(db, user_id)
    return FspSyncResponse(
        status="synced" if achievements else "no_history",
        provider=provider,
        fsp_member_id=link.fsp_member_id,
        last_synced_at=link.last_synced_at,
        is_stale=False,
        achievements_count=len(items),
        achievements=items,
    )


def is_snapshot_fresh(last_synced_at: datetime | None) -> bool:
    if last_synced_at is None:
        return False
    ttl = timedelta(hours=get_settings().fsp_cache_ttl_hours)
    return datetime.now(UTC) - last_synced_at <= ttl
