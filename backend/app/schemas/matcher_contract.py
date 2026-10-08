"""Backend ↔ ML Matcher contract (BE-001)."""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.schemas.common import MatchComponents


class MatcherNeed(BaseModel):
    specialization: str
    grade: str
    required_skills: list[str] = Field(default_factory=list)
    optional_skills: list[str] = Field(default_factory=list)
    salary_to: int | None = None
    work_format: str | None = None


class MatcherCandidateAchievement(BaseModel):
    type: str
    discipline: str | None = None
    result: str | None = None


class MatcherCandidate(BaseModel):
    id: str
    verified_specialization: str | None = None
    verified_grade: str | None = None
    test_score: int | None = None
    skills: list[str] = Field(default_factory=list)
    fsp_achievements: list[MatcherCandidateAchievement] = Field(default_factory=list)
    salary_min: int | None = None
    work_format: str | None = None


class MatchingRequest(BaseModel):
    need: MatcherNeed
    candidates: list[MatcherCandidate]


class MatcherMatch(BaseModel):
    candidate_id: str
    score: float
    components: MatchComponents
    matched_skills: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)
    reason_codes: list[str] = Field(default_factory=list)


class MatchingResponse(BaseModel):
    matches: list[MatcherMatch]
    model_version: str = "baseline-v1"
