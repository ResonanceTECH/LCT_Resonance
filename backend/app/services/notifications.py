"""In-app notifications (Backend.md: offer_new, offer_accepted, offer_declined, fsp_synced,
application, system). Created by the services that own the events, in their transaction."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError
from app.models.engagement import Notification
from app.models.enums import NotificationType
from app.schemas.engagement import NotificationOut, NotificationsResponse

LIST_LIMIT = 50


def notify(
    db: AsyncSession,
    *,
    user_id: UUID,
    type: NotificationType,
    title: str,
    body: str,
    href: str | None = None,
) -> None:
    """Queue a notification; it is saved with the caller's commit."""
    db.add(Notification(user_id=user_id, type=type.value, title=title, body=body, href=href))


async def unread_count(db: AsyncSession, user_id: UUID) -> int:
    result = await db.execute(
        select(func.count())
        .select_from(Notification)
        .where(Notification.user_id == user_id, Notification.read_at.is_(None))
    )
    return int(result.scalar_one())


async def list_notifications(db: AsyncSession, user_id: UUID) -> NotificationsResponse:
    rows = await db.execute(
        select(Notification)
        .where(Notification.user_id == user_id)
        .order_by(Notification.created_at.desc())
        .limit(LIST_LIMIT)
    )
    items = [
        NotificationOut(
            id=n.id,
            type=n.type,
            title=n.title,
            body=n.body,
            created_at=n.created_at,
            read=n.read_at is not None,
            href=n.href,
        )
        for n in rows.scalars().all()
    ]
    return NotificationsResponse(items=items, unread=await unread_count(db, user_id))


async def mark_read(db: AsyncSession, user_id: UUID, notification_id: UUID) -> None:
    result = await db.execute(
        update(Notification)
        .where(Notification.id == notification_id, Notification.user_id == user_id)
        .values(read_at=func.coalesce(Notification.read_at, datetime.now(UTC)))
        .returning(Notification.id)
    )
    if result.first() is None:
        raise AppError("NOTIFICATION_NOT_FOUND", "Уведомление не найдено", 404)
    await db.commit()


async def mark_all_read(db: AsyncSession, user_id: UUID) -> None:
    await db.execute(
        update(Notification)
        .where(Notification.user_id == user_id, Notification.read_at.is_(None))
        .values(read_at=datetime.now(UTC))
    )
    await db.commit()
