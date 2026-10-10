from __future__ import annotations

import asyncio
import json
from pathlib import Path

from app.integrations.fsp.base import FSPAchievementDTO, FSPMemberDTO, FSPUnavailableError

FIXTURES = Path(__file__).parent / "fixtures"


class MockFSPTimeoutError(FSPUnavailableError):
    pass


class MockFSPAdapter:
    """Synthetic FSP registry from JSON fixtures. `force_timeout` members simulate an outage."""

    def __init__(self) -> None:
        self._members = json.loads((FIXTURES / "members.json").read_text(encoding="utf-8"))
        self._achievements = json.loads(
            (FIXTURES / "achievements.json").read_text(encoding="utf-8")
        )

    async def get_member(self, member_id: str) -> FSPMemberDTO:
        data = self._members.get(member_id)
        if data and data.get("force_timeout"):
            await asyncio.sleep(3)
            raise MockFSPTimeoutError("simulated timeout")
        if data is None:
            return FSPMemberDTO(member_id=member_id, exists=False)
        return FSPMemberDTO(
            member_id=data["member_id"],
            display_name=data.get("display_name"),
            exists=True,
        )

    async def find_member(self, *, email: str, full_name: str | None) -> FSPMemberDTO | None:
        email_key = email.strip().casefold()
        name_key = (full_name or "").strip().casefold()
        for data in self._members.values():
            by_email = (data.get("email") or "").casefold() == email_key
            by_name = bool(name_key) and (data.get("display_name") or "").casefold() == name_key
            if by_email or by_name:
                return await self.get_member(data["member_id"])
        return None

    async def get_achievements(self, member_id: str) -> list[FSPAchievementDTO]:
        data = self._members.get(member_id)
        if data and data.get("force_timeout"):
            await asyncio.sleep(3)
            raise MockFSPTimeoutError("simulated timeout")
        rows = self._achievements.get(member_id, [])
        return [FSPAchievementDTO.model_validate(r) for r in rows]

    async def healthcheck(self) -> bool:
        return True
