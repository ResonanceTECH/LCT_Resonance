from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.common import IdName, ORMModel


class CandidateSkillIn(BaseModel):
    skill_id: UUID
    level: int = Field(default=3, ge=1, le=5)


class CandidateUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    phone: str | None = None
    telegram: str | None = None
    city: str | None = None
    bio: str | None = None
    experience_months: int | None = Field(default=None, ge=0)
    declared_specialization_id: UUID | None = None
    declared_grade_id: UUID | None = None
    salary_min: int | None = Field(default=None, ge=0)
    work_format: str | None = None
    open_to_offers: bool | None = None


class CandidateMeResponse(ORMModel):
    id: UUID
    first_name: str | None = None
    last_name: str | None = None
    phone: str | None = None
    telegram: str | None = None
    city: str | None = None
    bio: str | None = None
    experience_months: int | None = None
    declared_specialization: IdName | None = None
    declared_grade: IdName | None = None
    verified_specialization: IdName | None = None
    verified_grade: IdName | None = None
    grade_verification_status: str
    salary_min: int | None = None
    work_format: str | None = None
    open_to_offers: bool
    skills: list[str] = Field(default_factory=list)
    has_fsp_history: bool = False
    last_test_score: int | None = None


class CandidatePublicResponse(ORMModel):
    id: UUID
    display_name: str
    city: str | None = None
    bio: str | None = None
    experience_months: int | None = None
    specialization: str | None = None
    grade: str | None = None
    skills: list[str] = Field(default_factory=list)
    salary_min: int | None = None
    work_format: str | None = None
    open_to_offers: bool
    has_fsp_history: bool = False
    last_test_score: int | None = None
