"""Notifications, dashboards, analytics, admin and company DTOs (frontend types)."""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import EmailStr, Field

from app.schemas.auth import RoleValue
from app.schemas.candidate import ProfileCompleteness
from app.schemas.common import ApiModel, OptionalText, ReadinessValue

NotificationTypeValue = Literal[
    "offer_new", "offer_accepted", "offer_declined", "fsp_synced", "application", "system"
]


class NotificationOut(ApiModel):
    id: UUID
    type: NotificationTypeValue
    title: str
    body: str
    created_at: datetime
    read: bool
    href: str | None = None


class NotificationsResponse(ApiModel):
    items: list[NotificationOut]
    unread: int


class CandidateDashboard(ApiModel):
    profile_views: int
    offers_received: int
    offers_accepted: int
    profile_status: str
    fsp_sync_status: str
    completeness: ProfileCompleteness | None = None
    unread_notifications: int = 0
    saved_vacancies_count: int = 0
    applications_count: int = 0


class EmployerDashboard(ApiModel):
    candidates_found: int
    shortlist_size: int
    offers_sent: int
    offers_accepted: int
    unread_notifications: int = 0


class Funnel(ApiModel):
    viewed_candidates: int
    shortlisted: int
    offers_sent: int
    offers_accepted: int
    offers_declined: int


class Conversion(ApiModel):
    shortlist_rate: float
    offer_accept_rate: float


class SpecializationCount(ApiModel):
    specialization: str
    count: int


class ReadinessCount(ApiModel):
    readiness: ReadinessValue
    count: int


class SkillCount(ApiModel):
    skill: str
    count: int


class EmployerAnalytics(ApiModel):
    funnel: Funnel
    conversion: Conversion
    by_specialization: list[SpecializationCount]
    avg_match_score: int | None = None
    readiness_breakdown: list[ReadinessCount]
    top_skills: list[SkillCount]


class AdminOverview(ApiModel):
    users_total: int
    candidates: int
    employers: int
    vacancies_active: int
    offers_open: int
    offers_accepted: int
    blocked_users: int


class AdminUserRow(ApiModel):
    id: UUID
    email: str
    role: RoleValue
    display_name: str
    status: Literal["active", "blocked", "deleted"]


class AdminStatusUpdate(ApiModel):
    status: Literal["active", "blocked"]


class CompanyIn(ApiModel):
    name: str = Field(min_length=1, max_length=255)
    description: OptionalText = Field(default=None, max_length=5000)
    industry: OptionalText = Field(default=None, max_length=128)
    website: OptionalText = Field(default=None, max_length=512)
    contact_name: OptionalText = Field(default=None, max_length=128)
    contact_email: EmailStr | None = None


class CompanyOut(ApiModel):
    id: UUID
    name: str
    description: str | None = None
    industry: str | None = None
    website: str | None = None
    contact_name: str | None = None
    contact_email: str | None = None
