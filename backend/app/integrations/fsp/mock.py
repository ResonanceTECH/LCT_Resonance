from __future__ import annotations

import asyncio
import json
from pathlib import Path

from app.integrations.fsp.base import FSPAchievementDTO, FSPMemberDTO

FIXTURES = Path(__file__).parent / "fixtures"


class MockFSPTimeoutError(Exception):
    pass


class MockFSPAdapter:
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

    async def get_achievements(self, member_id: str) -> list[FSPAchievementDTO]:
        data = self._members.get(member_id)
        if data and data.get("force_timeout"):
            await asyncio.sleep(3)
            raise MockFSPTimeoutError("simulated timeout")
        rows = self._achievements.get(member_id, [])
        return [FSPAchievementDTO.model_validate(r) for r in rows]

    async def healthcheck(self) -> bool:
        return True
