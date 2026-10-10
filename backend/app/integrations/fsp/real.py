from __future__ import annotations

import httpx

from app.core.config import get_settings
from app.integrations.fsp.base import FSPAchievementDTO, FSPMemberDTO, FSPUnavailableError


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
            raise FSPUnavailableError("FSP_BASE_URL is not configured")
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.get(f"{self.base_url}/members/{member_id}", headers=self._headers())
        if resp.status_code == 404:
            return FSPMemberDTO(member_id=member_id, exists=False)
        resp.raise_for_status()
        data = resp.json()
        return FSPMemberDTO(
            member_id=str(data.get("id", member_id)),
            display_name=data.get("display_name"),
            exists=True,
        )

    async def find_member(self, *, email: str, full_name: str | None) -> FSPMemberDTO | None:
        # Assumed endpoint until the registry API is published; with FSP ID (Keycloak/OIDC)
        # the member id would come from the token instead of a lookup.
        if not self.base_url:
            raise FSPUnavailableError("FSP_BASE_URL is not configured")
        params = {"email": email, **({"full_name": full_name} if full_name else {})}
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.get(
                f"{self.base_url}/members", params=params, headers=self._headers()
            )
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        payload = resp.json()
        items = payload if isinstance(payload, list) else payload.get("items", [])
        if not items:
            return None
        first = items[0]
        return FSPMemberDTO(
            member_id=str(first["id"]), display_name=first.get("display_name"), exists=True
        )

    async def get_achievements(self, member_id: str) -> list[FSPAchievementDTO]:
        if not self.base_url:
            raise FSPUnavailableError("FSP_BASE_URL is not configured")
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
