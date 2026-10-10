from __future__ import annotations

import httpx

from app.schemas.matcher_contract import MatchingRequest, MatchingResponse


class HttpMatcher:
    """Client for the external ML ranking service (`POST {base_url}/rank`)."""

    name = "ml"

    def __init__(self, base_url: str, timeout_sec: float) -> None:
        self._url = f"{base_url.rstrip('/')}/rank"
        self._timeout = timeout_sec

    async def rank(self, request: MatchingRequest) -> MatchingResponse:
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.post(
                self._url, json=request.model_dump(mode="json", by_alias=True)
            )
        response.raise_for_status()
        return MatchingResponse.model_validate(response.json())
