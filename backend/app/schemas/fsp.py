from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class FspLinkRequest(BaseModel):
    fsp_member_id: str = Field(min_length=3, max_length=128)


class FspAchievementOut(BaseModel):
    id: UUID
    type: str
    competition_name: str | None = None
    discipline: str | None = None
    place: int | None = None
    result: str | None = None
    role: str | None = None
    sport_rank: str | None = None
    verified: bool = True


class FspSyncResponse(BaseModel):
    status: str
    provider: str
    fsp_member_id: str
    last_synced_at: datetime | None = None
    is_stale: bool = False
    achievements_count: int = 0
    achievements: list[FspAchievementOut] = Field(default_factory=list)
