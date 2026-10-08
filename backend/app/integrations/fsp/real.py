from __future__ import annotations

import httpx

from app.core.config import get_settings
from app.core.errors import AppError
from app.integrations.fsp.base import FSPAchievementDTO, FSPMemberDTO


class RealFSPAdapter:
    """Contractual stub until real FSP API is published."""

    def __init__(self) -> None:
        settings = get_settings()
        self.base_url = settings.fsp_base_url.rstrip("/")
        self.token = settings.fsp_api_token
        self.timeout = settings.fsp_timeout_sec

    def _headers(self) -> dict[str, str]:
        headers = {"Accept": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    async def get_member(self, member_id: str) -> FSPMemberDTO:
        if not self.base_url:
            raise AppError("FSP_NOT_CONFIGURED", "Real FSP provider is not configured", 503)
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.get(
                f"{self.base_url}/members/{member_id}", headers=self._headers()
            )
        if resp.status_code == 404:
            return FSPMemberDTO(member_id=member_id, exists=False)
        resp.raise_for_status()
        data = resp.json()
        return FSPMemberDTO(
            member_id=str(data.get("id", member_id)),
            display_name=data.get("display_name"),
            exists=True,
        )

    async def get_achievements(self, member_id: str) -> list[FSPAchievementDTO]:
        if not self.base_url:
            raise AppError("FSP_NOT_CONFIGURED", "Real FSP provider is not configured", 503)
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.get(
                f"{self.base_url}/members/{member_id}/achievements",
                headers=self._headers(),
            )
        if resp.status_code == 404:
            return []
        resp.raise_for_status()
        payload = resp.json()
        items = payload if isinstance(payload, list) else payload.get("items", [])
        return [FSPAchievementDTO.model_validate(i) for i in items]

    async def healthcheck(self) -> bool:
        if not self.base_url:
            return False
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.get(f"{self.base_url}/health", headers=self._headers())
            return resp.status_code < 500
        except httpx.HTTPError:
            return False
