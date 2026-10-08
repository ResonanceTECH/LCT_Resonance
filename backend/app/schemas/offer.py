from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from app.schemas.common import ORMModel


class EmployerContact(BaseModel):
    type: str = "email"
    value: str


class OfferCreate(BaseModel):
    candidate_id: UUID
    vacancy_id: UUID | None = None
    title: str
    description: str
    salary_from: int = Field(gt=0)
    salary_to: int = Field(gt=0)
    currency: str = "RUB"
    work_format: str = "remote"
    employer_contact: EmployerContact

    @model_validator(mode="after")
    def validate_salary(self) -> OfferCreate:
        if self.salary_to < self.salary_from:
            raise ValueError("salary_to must be >= salary_from")
        return self


class CompanyBrief(BaseModel):
    id: UUID
    name: str


class OfferOut(ORMModel):
    id: UUID
    candidate_id: UUID
    employer_user_id: UUID
    company: CompanyBrief
    vacancy_id: UUID | None = None
    title: str
    description: str
    salary_from: int
    salary_to: int
    currency: str
    work_format: str
    employer_contact: EmployerContact
    status: str
    created_at: datetime
    viewed_at: datetime | None = None
    responded_at: datetime | None = None


class CandidateContactOut(BaseModel):
    candidate_id: UUID
    contact: dict[str, str | None]
