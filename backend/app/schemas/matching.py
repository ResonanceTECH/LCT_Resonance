from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.common import MatchDTO


class NeedSkill(BaseModel):
    skill_id: UUID
    required: bool = True


class MatchingNeed(BaseModel):
    specialization_id: UUID
    grade_id: UUID
    salary_from: int | None = None
    salary_to: int | None = None
    work_format: str | None = None
    skills: list[NeedSkill] = Field(default_factory=list)


class MatchingSearchRequest(BaseModel):
    vacancy_id: UUID | None = None
    need: MatchingNeed | None = None
    limit: int = Field(default=20, ge=1, le=50)
    offset: int = Field(default=0, ge=0)


class MatchingCandidateCard(BaseModel):
    id: UUID
    display_name: str
    specialization: str | None = None
    grade: str | None = None
    skills: list[str] = Field(default_factory=list)
    has_fsp_history: bool = False


class MatchingItem(BaseModel):
    candidate: MatchingCandidateCard
    match: MatchDTO


class MatchingSearchResponse(BaseModel):
    items: list[MatchingItem]
    total: int
    limit: int
    offset: int
    matcher: str = "baseline"
