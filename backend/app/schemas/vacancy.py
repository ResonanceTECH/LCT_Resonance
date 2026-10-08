from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from app.schemas.common import ORMModel


class VacancySkillIn(BaseModel):
    skill_id: UUID
    required: bool = True
    weight: int | None = None


class VacancyCreate(BaseModel):
    title: str
    description: str
    specialization_id: UUID
    grade_id: UUID
    salary_from: int = Field(gt=0)
    salary_to: int = Field(gt=0)
    currency: str = "RUB"
    work_format: str = "remote"
    visibility: str = "private"
    skills: list[VacancySkillIn] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_salary(self) -> VacancyCreate:
        if self.salary_to < self.salary_from:
            raise ValueError("salary_to must be >= salary_from")
        return self


class VacancyUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    specialization_id: UUID | None = None
    grade_id: UUID | None = None
    salary_from: int | None = Field(default=None, gt=0)
    salary_to: int | None = Field(default=None, gt=0)
    currency: str | None = None
    work_format: str | None = None
    visibility: str | None = None
    skills: list[VacancySkillIn] | None = None


class VacancyOut(ORMModel):
    id: UUID
    company_id: UUID
    title: str
    description: str
    specialization_id: UUID
    grade_id: UUID
    salary_from: int
    salary_to: int
    currency: str
    work_format: str
    visibility: str
    status: str
    skills: list[VacancySkillIn] = Field(default_factory=list)
