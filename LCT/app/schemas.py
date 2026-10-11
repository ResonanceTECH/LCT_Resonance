"""Backend ↔ ML camelCase contract (+ ML-only endpoints)."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class ApiModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )


# ----- shared ranking contract (Backend.md) -----


class MatcherVacancy(ApiModel):
    id: str
    specialization: str
    required_grade: str
    required_skills: list[str] = Field(default_factory=list)
    nice_to_have_skills: list[str] = Field(default_factory=list)
    salary_from: int | None = None
    salary_to: int | None = None
    work_format: str | None = None


class MatcherFspAchievement(ApiModel):
    id: str = ""
    title: str = ""
    discipline: str | None = None
    place_or_result: str | None = None
    sport_rank: str | None = None
    verified: bool = True
    achievement_type: str = "participation"  # participation | finalist | prize


class MatcherCandidate(ApiModel):
    id: str
    specialization: str | None = None
    confirmed_grade: str | None = None
    # Declared grade is optional; Backend may omit it. ML never overwrites it (ML-03).
    declared_grade: str | None = None
    test_score: int | None = None
    skills: list[str] = Field(default_factory=list)
    experience_years: int | None = None
    experience_months: int | None = None
    salary_from: int | None = None
    salary_to: int | None = None
    work_format: str | None = None
    work_formats: list[str] = Field(default_factory=list)
    fsp_achievements: list[MatcherFspAchievement] = Field(default_factory=list)
    profile_completeness: float | None = None  # 0..100 if Backend knows it


class MatchingRequest(ApiModel):
    vacancy: MatcherVacancy
    candidates: list[MatcherCandidate]


class MatcherReason(ApiModel):
    code: str
    params: dict[str, Any] = Field(default_factory=dict)
    positive: bool = True


class MatchComponents(ApiModel):
    test: float = 0
    skills: float = 0
    fsp: float = 0
    conditions: float = 0
    # Optional diagnostics (ML.md weights); never required by Backend.
    specialization: float | None = None


class MatcherMatch(ApiModel):
    candidate_id: str
    score: float
    matched_skills: list[str] = Field(default_factory=list)
    missing_in_profile_skills: list[str] = Field(default_factory=list)
    reasons: list[MatcherReason] = Field(default_factory=list)
    components: MatchComponents | None = None
    category: str | None = None
    category_score: float | None = None
    grade_status: str | None = None
    salary_compatible: bool | None = None
    work_format_compatible: bool | None = None


class MatchingResponse(ApiModel):
    matches: list[MatcherMatch]
    model_version: str = "ml-v1"


# ----- ML-only endpoints -----


class NormalizeSkillsRequest(ApiModel):
    skills: list[str]


class NormalizeSkillsResponse(ApiModel):
    skills: list[str]


class CategorizeRequest(ApiModel):
    candidate_id: str | int | None = None
    specialization: str | None = None
    skills: list[str] = Field(default_factory=list)
    experience_months: int | None = None
    fsp_achievements: list[MatcherFspAchievement] = Field(default_factory=list)
    competition_roles: list[str] = Field(default_factory=list)


class CategorizeResponse(ApiModel):
    candidate_id: str | int | None = None
    category: str
    confidence: float
    reasons: list[str]


class GradeStatusRequest(ApiModel):
    declared_grade: str
    test_score: int | None = None
    pass_score: int = 70


class GradeStatusResponse(ApiModel):
    declared_grade: str
    test_score: int | None = None
    grade_status: str  # confirmed | not_confirmed | unknown


class CategoryRankRequest(ApiModel):
    candidates: list[MatcherCandidate]


class CategoryRankItem(ApiModel):
    category: str
    candidate_id: str
    category_score: float


class CategoryRankResponse(ApiModel):
    items: list[CategoryRankItem]
    model_version: str = "ml-v1"


# ----- catalog / online retrieval (mini-db). Backend keeps calling POST /rank. -----


class CatalogWriteResponse(ApiModel):
    id: str
    indexed_tokens: int


class ResumeCatalogResponse(ApiModel):
    items: list[MatcherCandidate]


class VacancyCatalogResponse(ApiModel):
    items: list[MatcherVacancy]


class OfflineRebuildResponse(ApiModel):
    indexed: int


class OnlineResumeRankRequest(ApiModel):
    vacancy: MatcherVacancy
    limit: int = Field(default=50, ge=1, le=500)


class OnlineResumeRankResponse(ApiModel):
    matches: list[MatcherMatch]
    model_version: str = "ml-v1"
    retrieved: int = 0


class OnlineVacancyRankRequest(ApiModel):
    candidate: MatcherCandidate
    limit: int = Field(default=20, ge=1, le=500)


class VacancyMatch(ApiModel):
    vacancy_id: str
    score: float
    matched_skills: list[str] = Field(default_factory=list)
    missing_in_profile_skills: list[str] = Field(default_factory=list)
    reasons: list[MatcherReason] = Field(default_factory=list)
    components: MatchComponents | None = None
    content_similarity: float = 0
    salary_compatible: bool | None = None
    work_format_compatible: bool | None = None


class OnlineVacancyRankResponse(ApiModel):
    matches: list[VacancyMatch]
    model_version: str = "ml-v1"
    retrieved: int = 0


class SimilarResumesRequest(ApiModel):
    candidate: MatcherCandidate
    limit: int = Field(default=10, ge=1, le=500)


class SimilarResume(ApiModel):
    candidate_id: str
    content_similarity: float
    category: str


class SimilarResumesResponse(ApiModel):
    items: list[SimilarResume]
    model_version: str = "ml-v1"


class MatchPairRequest(ApiModel):
    vacancy: MatcherVacancy
    candidate: MatcherCandidate
