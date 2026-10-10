from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import Field, model_validator

from app.schemas.candidate import CandidateMatch
from app.schemas.common import (
    ApiModel,
    Currency,
    GradeValue,
    OptionalText,
    WorkFormatValue,
    check_salary_range,
    reject_explicit_nulls,
)

VacancyStatusValue = Literal["draft", "active", "closed", "archived"]
SkillList = list[str]


class VacancyCreate(ApiModel):
    # Snapshot for the vacancy card; defaults to the employer's company profile name.
    company_name: OptionalText = Field(default=None, max_length=255)
    title: str = Field(min_length=1, max_length=255)
    description: str = Field(min_length=1, max_length=10000)
    specialization: str = Field(min_length=1, max_length=128)
    required_grade: GradeValue
    required_skills: SkillList = Field(default_factory=list, max_length=30)
    nice_to_have_skills: SkillList = Field(default_factory=list, max_length=30)
    salary_from: int
    salary_to: int
    currency: Currency = "RUB"
    city: OptionalText = Field(default=None, max_length=128)
    work_format: WorkFormatValue = "remote"
    extra_info: OptionalText = Field(default=None, max_length=5000)
    status: VacancyStatusValue = "draft"

    @model_validator(mode="after")
    def _validate(self) -> VacancyCreate:
        check_salary_range(self.salary_from, self.salary_to)
        return self


class VacancyUpdate(ApiModel):
    company_name: OptionalText = Field(default=None, max_length=255)
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, min_length=1, max_length=10000)
    specialization: str | None = Field(default=None, min_length=1, max_length=128)
    required_grade: GradeValue | None = None
    required_skills: SkillList | None = Field(default=None, max_length=30)
    nice_to_have_skills: SkillList | None = Field(default=None, max_length=30)
    salary_from: int | None = None
    salary_to: int | None = None
    currency: Currency | None = None
    city: OptionalText = Field(default=None, max_length=128)
    work_format: WorkFormatValue | None = None
    extra_info: OptionalText = Field(default=None, max_length=5000)
    status: VacancyStatusValue | None = None

    @model_validator(mode="after")
    def _validate(self) -> VacancyUpdate:
        reject_explicit_nulls(
            self,
            "title",
            "description",
            "specialization",
            "required_grade",
            "salary_from",
            "salary_to",
            "work_format",
            "status",
        )
        check_salary_range(self.salary_from, self.salary_to)
        return self


class VacancyOut(ApiModel):
    id: UUID
    employer_id: UUID
    company_name: str
    title: str
    description: str
    specialization: str
    required_grade: GradeValue
    required_skills: list[str]
    nice_to_have_skills: list[str]
    salary_from: int
    salary_to: int
    currency: str
    city: str | None = None
    work_format: WorkFormatValue
    extra_info: str | None = None
    status: VacancyStatusValue
    created_at: datetime
    updated_at: datetime


class VacancyWithMatch(VacancyOut):
    match: CandidateMatch | None = None
    saved: bool | None = None
    applied: bool | None = None


class VacancyParseRequest(ApiModel):
    text: str = Field(min_length=1, max_length=20000)


class VacancyParseResult(ApiModel):
    title: str | None = None
    description: str | None = None
    specialization: str | None = None
    required_grade: GradeValue | None = None
    required_skills: list[str] = Field(default_factory=list)
    nice_to_have_skills: list[str] = Field(default_factory=list)
    salary_from: int | None = None
    salary_to: int | None = None
    work_format: WorkFormatValue | None = None
    city: str | None = None


class ApplyResponse(ApiModel):
    ok: bool = True
    message: str


class SavedResponse(ApiModel):
    ok: bool = True
    saved: bool
