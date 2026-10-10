from __future__ import annotations

import datetime as dt
from typing import Literal
from uuid import UUID

from pydantic import Field

from app.schemas.common import ApiModel


class FspAchievementOut(ApiModel):
    id: UUID
    title: str
    discipline: str | None = None
    date: dt.date | None = None  # module alias: the field name shadows the type
    place_or_result: str | None = None
    participant_role: str | None = None
    sport_rank: str | None = None
    verified: Literal[True] = True


class FspAchievementsResponse(ApiModel):
    achievements: list[FspAchievementOut]
    synced_at: dt.datetime | None = None
    # Extra to the frontend type: synced | no_history (a normal 200) | stale (cache served).
    status: str = "none"


class FspLinkRequest(ApiModel):
    fsp_member_id: str = Field(min_length=3, max_length=128)


class FspLinkOut(ApiModel):
    fsp_member_id: str
    linked_at: dt.datetime
