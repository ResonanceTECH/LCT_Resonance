"""Backend ↔ ML matcher contract (Backend.md, "Backend ↔ ML контракт").

One batch call per ranking: a vacancy and its candidates in, scored matches out. JSON is
camelCase. The matcher returns reason codes with parameters; the backend renders labels.
"""

from __future__ import annotations

from typing import Any

from pydantic import Field

from app.schemas.common import ApiModel


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
    id: str
    title: str
    discipline: str | None = None
    place_or_result: str | None = None
    sport_rank: str | None = None
    verified: bool = True
    # participation | finalist | prize, derived by the backend from placeOrResult.
    achievement_type: str = "participation"


class MatcherCandidate(ApiModel):
    id: str
    specialization: str | None = None
    confirmed_grade: str | None = None
    test_score: int | None = None
    skills: list[str] = Field(default_factory=list)
    experience_years: int | None = None
    salary_from: int | None = None
    salary_to: int | None = None
    work_format: str | None = None
    fsp_achievements: list[MatcherFspAchievement] = Field(default_factory=list)


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


class MatcherMatch(ApiModel):
    candidate_id: str
    score: float
    matched_skills: list[str] = Field(default_factory=list)
    missing_in_profile_skills: list[str] = Field(default_factory=list)
    reasons: list[MatcherReason] = Field(default_factory=list)
    # For debugging and the defence; never sent to the frontend.
    components: MatchComponents | None = None


class MatchingResponse(ApiModel):
    matches: list[MatcherMatch]
    model_version: str = "baseline-v1"
