from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError
from app.models.enums import OfferStatus, UserRole, UserStatus, VacancyStatus
from app.models.offer import Offer
from app.models.user import AuthSession, User
from app.models.vacancy import Vacancy
from app.schemas.engagement import AdminOverview, AdminUserRow
from app.services.audit import write_audit


def _row(user: User) -> AdminUserRow:
    return AdminUserRow(
        id=user.id,
        email=user.email,
        role=user.role,
        display_name=user.display_name,
        status=user.status,
    )


async def overview(db: AsyncSession) -> AdminOverview:
    roles = dict((await db.execute(select(User.role, func.count()).group_by(User.role))).all())
    blocked = await db.execute(
        select(func.count()).select_from(User).where(User.status == UserStatus.blocked.value)
    )
    active_vacancies = await db.execute(
        select(func.count())
        .select_from(Vacancy)
        .where(Vacancy.status == VacancyStatus.active.value)
    )
    offers = dict(
        (await db.execute(select(Offer.status, func.count()).group_by(Offer.status))).all()
    )
    candidates = roles.get(UserRole.candidate.value, 0)
    employers = roles.get(UserRole.employer.value, 0)
    return AdminOverview(
        users_total=candidates + employers,
        candidates=candidates,
        employers=employers,
        vacancies_active=int(active_vacancies.scalar_one()),
        offers_open=offers.get(OfferStatus.new.value, 0) + offers.get(OfferStatus.viewed.value, 0),
        offers_accepted=offers.get(OfferStatus.accepted.value, 0),
        blocked_users=int(blocked.scalar_one()),
    )


async def list_users(db: AsyncSession) -> list[AdminUserRow]:
    rows = await db.execute(
        select(User).where(User.role != UserRole.admin.value).order_by(User.created_at.desc())
    )
    return [_row(u) for u in rows.scalars().all()]


async def set_status(db: AsyncSession, admin: User, user_id: UUID, status: str) -> AdminUserRow:
    user = await db.get(User, user_id)
    if user is None or user.role == UserRole.admin.value:
        raise AppError("USER_NOT_FOUND", "Пользователь не найден", 404)
    user.status = status
    if status == UserStatus.blocked.value:
        # A blocked account must lose access at once, not when its token expires.
        await db.execute(
            update(AuthSession)
            .where(AuthSession.user_id == user_id, AuthSession.revoked_at.is_(None))
            .values(revoked_at=datetime.now(UTC))
        )
    await write_audit(
        db,
        action="USER_STATUS_CHANGED",
        entity_type="user",
        entity_id=str(user_id),
        actor_user_id=admin.id,
        metadata={"status": status},
    )
    await db.commit()
    return _row(user)
