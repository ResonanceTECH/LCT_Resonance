from __future__ import annotations

from datetime import datetime
from typing import Protocol

from pydantic import BaseModel


class FSPMemberDTO(BaseModel):
    member_id: str
    display_name: str | None = None
    exists: bool = True


class FSPAchievementDTO(BaseModel):
    external_id: str
    achievement_type: str
    discipline: str | None = None
    competition_name: str | None = None
    result: str | None = None
    place: int | None = None
    role: str | None = None
    sport_rank: str | None = None
    achieved_at: datetime | None = None


class FSPAdapter(Protocol):
    async def get_member(self, member_id: str) -> FSPMemberDTO: ...

    async def get_achievements(self, member_id: str) -> list[FSPAchievementDTO]: ...

    async def healthcheck(self) -> bool: ...
