from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class Page(BaseModel, Generic[T]):
    items: list[T]
    total: int
    limit: int = 20
    offset: int = 0


class IdName(ORMModel):
    id: str
    name: str


class Reason(BaseModel):
    code: str
    text: str


class MatchComponents(BaseModel):
    test: float = 0
    skills: float = 0
    fsp: float = 0
    conditions: float = 0


class MatchDTO(BaseModel):
    score: float
    components: MatchComponents
    matched_skills: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)
    reasons: list[Reason] = Field(default_factory=list)
