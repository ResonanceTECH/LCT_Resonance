from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import Field, model_validator

from app.schemas.common import (
    ApiModel,
    Currency,
    GradeValue,
    MatchReason,
    OptionalSalary,
    OptionalText,
    ReadinessValue,
    WorkFormatValue,
    check_salary_range,
    reject_explicit_nulls,
)
from app.schemas.fsp import FspAchievementOut


class TestResultSummary(ApiModel):
    score: int
    max_score: int = 100
    grade_confirmed: bool
    completed_at: datetime


class CandidateProfileOut(ApiModel):
    """`CandidateProfile` of the frontend. Never carries contacts."""

    id: UUID
    user_id: UUID
    full_name: str
    about: str | None = None
    specialization: str
    claimed_grade: GradeValue
    confirmed_grade: GradeValue | None = None
    experience_years: int | None = None
    experience_description: str | None = None
    skills: list[str] = Field(default_factory=list)
    desired_position: str | None = None
    salary_from: int | None = None
    salary_to: int | None = None
    currency: str = "RUB"
    city: str | None = None
    work_format: WorkFormatValue | None = None
    readiness: ReadinessValue
    test_result: TestResultSummary | None = None
    fsp_synced_at: datetime | None = None
    has_fsp_achievements: bool = False
    profile_completeness: int = 0


class CandidateMeOut(CandidateProfileOut):
    """The owner's own profile: the only place phone and telegram are returned."""

    phone: str | None = None
    telegram: str | None = None
    email_verified: bool = False


class CandidateUpdate(ApiModel):
    """PATCH /candidates/me. Computed fields (confirmedGrade, testResult, ...) are ignored."""

    full_name: OptionalText = Field(default=None, max_length=255)
    about: OptionalText = Field(default=None, max_length=5000)
    specialization: OptionalText = None
    claimed_grade: GradeValue | None = None
    experience_years: int | None = Field(default=None, ge=0, le=60)
    experience_description: OptionalText = Field(default=None, max_length=5000)
    skills: list[str] | None = Field(default=None, max_length=50)
    desired_position: OptionalText = Field(default=None, max_length=255)
    salary_from: OptionalSalary = None
    salary_to: OptionalSalary = None
    currency: Currency | None = None
    city: OptionalText = Field(default=None, max_length=128)
    work_format: WorkFormatValue | None = None
    readiness: ReadinessValue | None = None
    phone: OptionalText = Field(default=None, max_length=64)
    telegram: OptionalText = Field(default=None, max_length=128)

    @model_validator(mode="after")
    def _validate(self) -> CandidateUpdate:
        reject_explicit_nulls(self, "full_name", "specialization", "claimed_grade", "readiness")
        check_salary_range(self.salary_from, self.salary_to)
        return self


class CandidateMatch(ApiModel):
    candidate_id: UUID
    vacancy_id: UUID
    score: int
    matched_skills: list[str] = Field(default_factory=list)
    # "Not listed in the profile", not "the candidate lacks the skill" (ML-06).
    missing_in_profile_skills: list[str] = Field(default_factory=list)
    reasons: list[MatchReason] = Field(default_factory=list)
    relevant_fsp: list[FspAchievementOut] = Field(default_factory=list)


class TalentPoolItem(CandidateProfileOut):
    match: CandidateMatch | None = None


class TalentPoolResponse(ApiModel):
    items: list[TalentPoolItem]
    total: int


class CandidateContacts(ApiModel):
    email: str | None = None
    phone: str | None = None
    telegram: str | None = None


class ProfileCompletenessItem(ApiModel):
    key: str
    label: str
    done: bool
    weight: int
    href: str | None = None


class ProfileCompleteness(ApiModel):
    percent: int
    items: list[ProfileCompletenessItem]


class SkillRadarAxis(ApiModel):
    skill: str
    score: int


class SkillRadar(ApiModel):
    candidate_id: UUID
    axes: list[SkillRadarAxis]


class SkillMatrixRow(ApiModel):
    skill: str
    # Keyed by candidate id; null = the skill is not listed in that profile.
    values: dict[str, int | None]


class CandidateCompareResponse(ApiModel):
    candidates: list[CandidateProfileOut]
    skill_matrix: list[SkillMatrixRow]
    radars: list[SkillRadar]


class PublicPassport(ApiModel):
    profile: CandidateProfileOut
    achievements: list[FspAchievementOut]
    radar: SkillRadar
    public_url: str


class ShortlistAdd(ApiModel):
    candidate_id: UUID
