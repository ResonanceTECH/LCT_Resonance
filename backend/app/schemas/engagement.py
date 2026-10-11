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


AdminEventTypeValue = Literal[
    "test_completed",
    "offer_sent",
    "user_registered",
    "user_blocked",
    "category_confirmed",
]


class AdminEvent(ApiModel):
    id: str
    type: AdminEventTypeValue
    title: str
    description: str | None = None
    created_at: datetime
    href: str | None = None


class AdminOverview(ApiModel):
    users_total: int
    candidates: int
    employers: int
    vacancies_active: int
    offers_open: int
    offers_accepted: int
    blocked_users: int
    confirmed_categories: int | None = None
    assessments_completed: int | None = None
    offers_total: int | None = None
    recent_events: list[AdminEvent] | None = None
    api_status: Literal["ok", "degraded", "down"] | None = "ok"


class AdminUserRow(ApiModel):
    id: UUID
    email: str
    role: RoleValue
    display_name: str
    status: Literal["active", "blocked", "deleted"]
    created_at: datetime | None = None
    specialization: str | None = None
    confirmed_grade: str | None = None
    claimed_grade: str | None = None
    test_status: Literal["none", "passed", "failed", "in_progress"] | None = None
    has_fsp_id: bool | None = None
    block_reason: str | None = None


class AdminStatusUpdate(ApiModel):
    status: Literal["active", "blocked"]
    reason: str | None = None


class AdminTestTopic(ApiModel):
    name: str
    difficulty: Literal["easy", "medium", "hard"]
    count: int


class AdminTestCatalogItem(ApiModel):
    id: str
    specialization: str
    grade: str
    question_count: int
    status: Literal["active", "draft", "archived"]
    topics: list[AdminTestTopic]


class AdminQuestionTemplate(ApiModel):
    id: str
    specialization: str
    topic: str
    difficulty: Literal["easy", "medium", "hard"]
    parameterized: bool
    active: bool
    prompt_preview: str


class AdminAttemptRow(ApiModel):
    id: str
    user_id: str
    display_name: str
    specialization: str
    grade: str
    score: int
    max_score: int
    passed: bool
    completed_at: datetime
    next_retest_at: datetime | None = None


class AdminScoreBucket(ApiModel):
    bucket: str
    count: int


class AdminAssessmentStats(ApiModel):
    success_rate: float
    total_attempts: int
    score_distribution: list[AdminScoreBucket]


class AdminAssessmentsResponse(ApiModel):
    catalog: list[AdminTestCatalogItem]
    templates: list[AdminQuestionTemplate]
    attempts: list[AdminAttemptRow]
    stats: AdminAssessmentStats


class AdminCategoryRow(ApiModel):
    id: str
    specialization: str
    grade: str
    confirmed_candidates: int


class AdminTaxonomySkill(ApiModel):
    id: str
    name: str
    aliases: list[str] | None = None


class AdminSpecializationRef(ApiModel):
    id: str
    name: str


class AdminGradeRef(ApiModel):
    id: str
    code: str
    name: str


class AdminIndustryRef(ApiModel):
    id: str
    name: str


class AdminCategoriesResponse(ApiModel):
    categories: list[AdminCategoryRow]
    specializations: list[AdminSpecializationRef]
    grades: list[AdminGradeRef]
    skills: list[AdminTaxonomySkill]
    industries: list[AdminIndustryRef]


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
