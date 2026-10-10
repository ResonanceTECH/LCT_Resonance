from __future__ import annotations

from uuid import UUID

from app.schemas.common import ApiModel


class SpecializationOut(ApiModel):
    id: UUID
    slug: str
    name: str


class GradeOut(ApiModel):
    id: UUID
    code: str
    rank: int
    name: str


class SkillOut(ApiModel):
    id: UUID
    slug: str
    name: str
