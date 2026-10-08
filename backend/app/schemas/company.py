from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from app.schemas.common import ORMModel


class CompanyCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    industry: str | None = None
    website: str | None = None
    contact_name: str | None = None
    contact_email: EmailStr | None = None


class CompanyUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    industry: str | None = None
    website: str | None = None
    contact_name: str | None = None
    contact_email: EmailStr | None = None


class CompanyOut(ORMModel):
    id: UUID
    name: str
    description: str | None = None
    industry: str | None = None
    website: str | None = None
    contact_name: str | None = None
    contact_email: str | None = None
    owner_user_id: UUID
