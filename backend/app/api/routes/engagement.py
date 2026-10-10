"""Notifications, dashboards, admin and the public Career Passport."""

from uuid import UUID

from fastapi import APIRouter

from app.core.deps import AdminUser, CandidateUser, CurrentUser, DbSession, EmployerUser
from app.schemas.candidate import PublicPassport
from app.schemas.common import OkResponse
from app.schemas.engagement import (
    AdminOverview,
    AdminStatusUpdate,
    AdminUserRow,
    CandidateDashboard,
    EmployerAnalytics,
    EmployerDashboard,
    NotificationsResponse,
)
from app.schemas.offer import OfferOut
from app.schemas.vacancy import VacancyOut
from app.services import admin, dashboards, insights, notifications, offers, vacancies

notifications_router = APIRouter(prefix="/notifications", tags=["notifications"])
dashboard_router = APIRouter(prefix="/dashboard", tags=["dashboard"])
admin_router = APIRouter(prefix="/admin", tags=["admin"])
public_router = APIRouter(prefix="/public", tags=["public"])


@notifications_router.get("", response_model=NotificationsResponse)
async def list_notifications(db: DbSession, user: CurrentUser) -> NotificationsResponse:
    return await notifications.list_notifications(db, user.id)


@notifications_router.post("/read-all", response_model=OkResponse)
async def read_all(db: DbSession, user: CurrentUser) -> OkResponse:
    await notifications.mark_all_read(db, user.id)
    return OkResponse()


@notifications_router.post("/{notification_id}/read", response_model=OkResponse)
async def read_one(notification_id: UUID, db: DbSession, user: CurrentUser) -> OkResponse:
    await notifications.mark_read(db, user.id, notification_id)
    return OkResponse()


@dashboard_router.get("/candidate", response_model=CandidateDashboard)
async def candidate_dashboard(db: DbSession, user: CandidateUser) -> CandidateDashboard:
    return await dashboards.candidate_dashboard(db, user)


@dashboard_router.get("/employer", response_model=EmployerDashboard)
async def employer_dashboard(db: DbSession, user: EmployerUser) -> EmployerDashboard:
    return await dashboards.employer_dashboard(db, user)


@dashboard_router.get("/employer/analytics", response_model=EmployerAnalytics)
async def employer_analytics(db: DbSession, user: EmployerUser) -> EmployerAnalytics:
    return await dashboards.employer_analytics(db, user)


@admin_router.get("/overview", response_model=AdminOverview)
async def admin_overview(db: DbSession, user: AdminUser) -> AdminOverview:
    return await admin.overview(db)


@admin_router.get("/users", response_model=list[AdminUserRow])
async def admin_users(db: DbSession, user: AdminUser) -> list[AdminUserRow]:
    return await admin.list_users(db)


@admin_router.post("/users/{user_id}/status", response_model=AdminUserRow)
async def admin_set_status(
    user_id: UUID, payload: AdminStatusUpdate, db: DbSession, user: AdminUser
) -> AdminUserRow:
    """Blocking also ends the user's sessions at once."""
    return await admin.set_status(db, user, user_id, payload.status)


@admin_router.get("/offers", response_model=list[OfferOut])
async def admin_offers(db: DbSession, user: AdminUser) -> list[OfferOut]:
    return await offers.list_all(db)


@admin_router.get("/vacancies", response_model=list[VacancyOut])
async def admin_vacancies(db: DbSession, user: AdminUser) -> list[VacancyOut]:
    return await vacancies.list_all(db)


@public_router.get("/passports/{slug}", response_model=PublicPassport)
async def career_passport(slug: str, db: DbSession) -> PublicPassport:
    """No auth. Shown only with the candidate's consent to profile publication."""
    return await insights.passport(db, slug)
