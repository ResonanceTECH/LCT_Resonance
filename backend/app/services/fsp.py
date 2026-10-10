from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable
from datetime import UTC, datetime
from uuid import UUID

import httpx
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.errors import AppError, integrity_constraint_name
from app.integrations.fsp import FSPUnavailableError, get_fsp_adapter
from app.integrations.fsp.base import FSPAchievementDTO, FSPMemberDTO
from app.models.candidate import CandidateProfile
from app.models.enums import ConsentType, FspSyncStatus, NotificationType
from app.models.fsp import FspAchievement, FspLink
from app.models.user import User
from app.schemas.fsp import FspAchievementOut, FspAchievementsResponse, FspLinkOut
from app.services.audit import write_audit
from app.services.consents import require_consent
from app.services.notifications import notify

logger = logging.getLogger("app.fsp")

FSP_SOURCE = "fsp"
# What counts as "the registry is down": the cached snapshot is served instead (stale).
_PROVIDER_ERRORS = (FSPUnavailableError, TimeoutError, httpx.HTTPError)


def _fsp_unavailable() -> AppError:
    return AppError("FSP_UNAVAILABLE", "Реестр ФСП временно недоступен, попробуйте позже", 503)


def _already_linked() -> AppError:
    return AppError("FSP_ID_ALREADY_LINKED", "Этот ID ФСП уже привязан к другому аккаунту", 409)


async def _call_registry[T](call: Awaitable[T]) -> T:
    """Registry calls are bounded by FSP_TIMEOUT_SEC (Backend.md: 2 s)."""
    return await asyncio.wait_for(call, timeout=get_settings().fsp_timeout_sec)


async def _delete_synced_achievements(db: AsyncSession, user_id: UUID) -> None:
    await db.execute(
        delete(FspAchievement).where(
            FspAchievement.candidate_user_id == user_id,
            FspAchievement.source == FSP_SOURCE,
        )
    )


def to_achievement_out(a: FspAchievement) -> FspAchievementOut:
    return FspAchievementOut(
        id=a.id,
        title=a.competition_name or a.discipline or "Достижение ФСП",
        discipline=a.discipline,
        date=a.achieved_at.date() if a.achieved_at else None,
        place_or_result=a.result,
        participant_role=a.role,
        sport_rank=a.sport_rank,
    )


async def list_achievements(db: AsyncSession, user_id: UUID) -> list[FspAchievementOut]:
    result = await db.execute(
        select(FspAchievement)
        .where(FspAchievement.candidate_user_id == user_id, FspAchievement.verified.is_(True))
        .order_by(FspAchievement.achieved_at.desc().nulls_last())
    )
    return [to_achievement_out(a) for a in result.scalars().all()]


def _status(link: FspLink | None, has_items: bool) -> FspSyncStatus:
    if link is None or link.last_synced_at is None:
        return FspSyncStatus.none
    if link.sync_status == FspSyncStatus.stale.value:
        return FspSyncStatus.stale
    return FspSyncStatus.synced if has_items else FspSyncStatus.no_history


async def achievements_response(db: AsyncSession, user_id: UUID) -> FspAchievementsResponse:
    link = await db.get(FspLink, user_id)
    items = await list_achievements(db, user_id)
    return FspAchievementsResponse(
        achievements=items,
        synced_at=link.last_synced_at if link else None,
        status=_status(link, bool(items)).value,
    )


async def _ensure_member_free(db: AsyncSession, member_id: str, user_id: UUID) -> None:
    owner = await db.execute(
        select(FspLink.candidate_user_id).where(FspLink.fsp_member_id == member_id)
    )
    owner_id = owner.scalar_one_or_none()
    if owner_id is not None and owner_id != user_id:
        raise _already_linked()


async def _commit_link(db: AsyncSession) -> None:
    try:
        await db.commit()
    except IntegrityError as exc:
        # Another account linked the same member between our check and the insert.
        await db.rollback()
        if integrity_constraint_name(exc) == "fsp_links_fsp_member_id_key":
            raise _already_linked() from exc
        raise


async def _attach(db: AsyncSession, user_id: UUID, member_id: str, *, how: str) -> FspLink:
    """Create or repoint the link (no commit)."""
    link = await db.get(FspLink, user_id)
    if link is None:
        link = FspLink(candidate_user_id=user_id, fsp_member_id=member_id)
        db.add(link)
    elif link.fsp_member_id != member_id:
        # A different member: achievements of the previous one must not stay attached.
        await _delete_synced_achievements(db, user_id)
        link.fsp_member_id = member_id
        link.sync_status = FspSyncStatus.none.value
        link.last_synced_at = None
        link.raw_snapshot = None
    await write_audit(
        db,
        action="FSP_LINKED",
        entity_type="fsp_link",
        entity_id=str(user_id),
        actor_user_id=user_id,
        metadata={"fsp_member_id": member_id, "how": how},
    )
    return link


async def link_fsp(db: AsyncSession, *, user_id: UUID, fsp_member_id: str) -> FspLinkOut:
    """Explicit link by FSP member id (in production it would come from FSP ID / OIDC)."""
    await require_consent(db, user_id, ConsentType.fsp_sync)
    await _ensure_member_free(db, fsp_member_id, user_id)
    try:
        member = await _call_registry(get_fsp_adapter().get_member(fsp_member_id))
    except _PROVIDER_ERRORS as exc:
        raise _fsp_unavailable() from exc
    if not member.exists:
        raise AppError("FSP_MEMBER_NOT_FOUND", "Участник ФСП не найден", 404)

    link = await _attach(db, user_id, fsp_member_id, how="manual")
    await _commit_link(db)
    await db.refresh(link)
    return FspLinkOut(fsp_member_id=link.fsp_member_id, linked_at=link.created_at)


async def drop_fsp_data(db: AsyncSession, user_id: UUID) -> bool:
    """Remove the link and synced achievements (no commit). Returns whether a link existed."""
    link = await db.get(FspLink, user_id)
    if link is None:
        return False
    await db.delete(link)
    await _delete_synced_achievements(db, user_id)
    await write_audit(
        db,
        action="FSP_UNLINKED",
        entity_type="fsp_link",
        entity_id=str(user_id),
        actor_user_id=user_id,
    )
    return True


async def unlink_fsp(db: AsyncSession, *, user_id: UUID) -> None:
    if await drop_fsp_data(db, user_id):
        await db.commit()


async def _replace_achievements(
    db: AsyncSession, user_id: UUID, incoming: list[FSPAchievementDTO]
) -> None:
    """Upsert by external_id and drop rows the registry no longer reports."""
    result = await db.execute(
        select(FspAchievement).where(
            FspAchievement.candidate_user_id == user_id,
            FspAchievement.source == FSP_SOURCE,
        )
    )
    current = {row.external_id: row for row in result.scalars().all()}
    incoming_ids = {dto.external_id for dto in incoming}
    for external_id, row in current.items():
        if external_id not in incoming_ids:
            await db.delete(row)

    for dto in incoming:
        row = current.get(dto.external_id)
        if row is None:
            row = FspAchievement(
                candidate_user_id=user_id, source=FSP_SOURCE, external_id=dto.external_id
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


async def _sync_response(
    db: AsyncSession, user_id: UUID, link: FspLink | None, status: FspSyncStatus
) -> FspAchievementsResponse:
    items = await list_achievements(db, user_id) if link else []
    return FspAchievementsResponse(
        achievements=items,
        synced_at=link.last_synced_at if link else datetime.now(UTC),
        status=status.value,
    )


async def _auto_link(db: AsyncSession, user: User) -> FspLink | None:
    """Find the candidate in the registry by account email and full name (Backend.md).

    None means the person is not an FSP member: a normal case, not an error.
    """
    profile = await db.get(CandidateProfile, user.id)
    full_name = profile.full_name if profile else ""
    member = await _call_registry(
        get_fsp_adapter().find_member(email=user.email, full_name=full_name or None)
    )
    if member is None:
        return None
    await _ensure_member_free(db, member.member_id, user.id)
    return await _attach(db, user.id, member.member_id, how="auto")


async def sync_fsp(db: AsyncSession, *, user: User) -> FspAchievementsResponse:
    await require_consent(db, user.id, ConsentType.fsp_sync)
    link = await db.get(FspLink, user.id)
    try:
        if link is None:
            link = await _auto_link(db, user)
            if link is None:
                # No FSP history must not block the profile (ТЗ): 200 with an empty list.
                return await _sync_response(db, user.id, None, FspSyncStatus.no_history)
        member: FSPMemberDTO = await _call_registry(
            get_fsp_adapter().get_member(link.fsp_member_id)
        )
        achievements: list[FSPAchievementDTO] = (
            await _call_registry(get_fsp_adapter().get_achievements(link.fsp_member_id))
            if member.exists
            else []
        )
    except _PROVIDER_ERRORS as exc:
        logger.warning("fsp_sync_failed", extra={"error": type(exc).__name__})
        if link is None or link.raw_snapshot is None:
            raise _fsp_unavailable() from exc
        # Registry is down but an earlier snapshot exists: serve it, marked as stale.
        link.sync_status = FspSyncStatus.stale.value
        await db.commit()
        return await _sync_response(db, user.id, link, FspSyncStatus.stale)

    await _replace_achievements(db, user.id, achievements)
    status = FspSyncStatus.synced if achievements else FspSyncStatus.no_history
    link.sync_status = status.value
    link.last_synced_at = datetime.now(UTC)
    link.raw_snapshot = {
        "member": member.model_dump(mode="json"),
        "achievements": [a.model_dump(mode="json") for a in achievements],
    }
    await write_audit(
        db,
        action="FSP_SYNCED",
        entity_type="fsp_link",
        entity_id=str(user.id),
        actor_user_id=user.id,
        metadata={"status": status.value, "count": len(achievements)},
    )
    notify(
        db,
        user_id=user.id,
        type=NotificationType.fsp_synced,
        title="ФСП синхронизирован",
        body=(
            f"Подтверждённых достижений: {len(achievements)}. Они видны работодателям."
            if achievements
            else "В реестре ФСП нет достижений — это не мешает подбору."
        ),
        href="/candidate/fsp",
    )
    await _commit_link(db)
    return await _sync_response(db, user.id, link, status)
