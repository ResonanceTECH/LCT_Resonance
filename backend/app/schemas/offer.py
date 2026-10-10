from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import Field, field_validator, model_validator

from app.schemas.common import (
    ApiModel,
    Currency,
    OptionalText,
    WorkFormatValue,
    check_salary_range,
)

OfferStatusValue = Literal["new", "viewed", "accepted", "declined", "withdrawn"]


class EmployerContact(ApiModel):
    type: Literal["email", "phone", "telegram", "url"] = "email"
    value: str = Field(min_length=1, max_length=320)


class OfferCreate(ApiModel):
    # Optional by ТЗ: an employer may approach a person without a published vacancy.
    vacancy_id: UUID | None = None
    candidate_id: UUID
    company_name: OptionalText = Field(default=None, max_length=255)
    position_title: str = Field(min_length=1, max_length=255)
    # Salary is mandatory: the candidate must see it before any conversation (ТЗ).
    salary_from: int
    salary_to: int
    currency: Currency = "RUB"
    work_format: WorkFormatValue = "remote"
    message: str = Field(min_length=1, max_length=5000)
    # Falls back to the employer account email when omitted.
    employer_contact: EmployerContact | None = None

    @field_validator("vacancy_id", mode="before")
    @classmethod
    def _blank_vacancy(cls, value: object) -> object:
        return None if value == "" else value

    @model_validator(mode="after")
    def _validate(self) -> OfferCreate:
        check_salary_range(self.salary_from, self.salary_to)
        return self


class OfferOut(ApiModel):
    id: UUID
    vacancy_id: UUID | None = None
    candidate_id: UUID
    employer_id: UUID
    employer_name: str
    employer_contact: EmployerContact
    company_name: str
    position_title: str
    salary_from: int
    salary_to: int
    currency: str
    work_format: WorkFormatValue
    message: str
    status: OfferStatusValue
    created_at: datetime
    viewed_at: datetime | None = None
    responded_at: datetime | None = None
