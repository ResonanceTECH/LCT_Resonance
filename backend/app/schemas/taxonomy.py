from __future__ import annotations

from uuid import UUID

from app.schemas.common import ORMModel


class SpecializationOut(ORMModel):
    id: UUID
    slug: str
    name: str


class GradeOut(ORMModel):
    id: UUID
    code: str
    rank: int
    name: str


class SkillOut(ORMModel):
    id: UUID
    slug: str
    name: str
