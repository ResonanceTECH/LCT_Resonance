from __future__ import annotations

from datetime import datetime
from typing import Protocol

from pydantic import BaseModel


class FSPUnavailableError(Exception):
    """The FSP registry could not be reached or is not configured."""


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
    """Adapters raise `FSPUnavailableError` (or time out) when the registry is down."""

    async def get_member(self, member_id: str) -> FSPMemberDTO: ...

    async def find_member(self, *, email: str, full_name: str | None) -> FSPMemberDTO | None:
        """Look a person up by account email (then full name); None if not a member."""
        ...

    async def get_achievements(self, member_id: str) -> list[FSPAchievementDTO]: ...

    async def healthcheck(self) -> bool: ...
