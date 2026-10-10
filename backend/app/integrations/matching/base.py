from __future__ import annotations

from typing import Protocol

from app.schemas.matcher_contract import MatchingRequest, MatchingResponse


class Matcher(Protocol):
    """Ranks a batch of candidates for one need. Implementations: baseline, ML over HTTP."""

    name: str

    async def rank(self, request: MatchingRequest) -> MatchingResponse: ...
