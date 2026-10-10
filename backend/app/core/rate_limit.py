"""In-process sliding-window rate limiting (Backend.md, "Безопасность").

Limits live in memory of one process, which fits the single-instance hackathon stand.
Behind nginx the client address comes from X-Forwarded-For via uvicorn `--proxy-headers`;
without it every user would share the proxy's address and one bucket.
"""

from __future__ import annotations

import math
import time
from collections import defaultdict, deque
from collections.abc import Awaitable, Callable

from fastapi import Depends, Request

from app.core.config import get_settings
from app.core.deps import CurrentUser
from app.core.errors import AppError

MINUTE = 60
DAY = 24 * 60 * 60


class SlidingWindowLimiter:
    # Keys with no recent hits are dropped once the table grows past this size.
    _SWEEP_THRESHOLD = 10_000

    def __init__(self, clock: Callable[[], float] = time.monotonic) -> None:
        self._clock = clock
        self._hits: defaultdict[str, deque[float]] = defaultdict(deque)

    def hit(self, key: str, *, limit: int, window_sec: float) -> float | None:
        """Record a hit. Returns seconds to wait if the limit is exceeded, else None."""
        now = self._clock()
        hits = self._hits[key]
        while hits and hits[0] <= now - window_sec:
            hits.popleft()
        if len(hits) >= limit:
            return hits[0] + window_sec - now
        hits.append(now)
        if len(self._hits) > self._SWEEP_THRESHOLD:
            self._sweep(now, window_sec)
        return None

    def _sweep(self, now: float, window_sec: float) -> None:
        stale = [k for k, hits in self._hits.items() if not hits or hits[-1] <= now - window_sec]
        for key in stale:
            del self._hits[key]

    def reset(self) -> None:
        self._hits.clear()


limiter = SlidingWindowLimiter()


def _check(key: str, limit: int, window_sec: float) -> None:
    if not get_settings().rate_limit_enabled:
        return
    retry_after = limiter.hit(key, limit=limit, window_sec=window_sec)
    if retry_after is not None:
        seconds = max(1, math.ceil(retry_after))
        raise AppError(
            "RATE_LIMITED",
            f"Слишком много запросов, повторите через {seconds} с",
            429,
            {"retry_after_sec": seconds},
            headers={"Retry-After": str(seconds)},
        )


def limit_by_ip(scope: str, limit: int, window_sec: float) -> Callable[..., Awaitable[None]]:
    async def dependency(request: Request) -> None:
        client = request.client.host if request.client else "unknown"
        _check(f"{scope}:ip:{client}", limit, window_sec)

    return dependency


def limit_by_user(scope: str, limit: int, window_sec: float) -> Callable[..., Awaitable[None]]:
    async def dependency(user: CurrentUser) -> None:
        _check(f"{scope}:user:{user.id}", limit, window_sec)

    return dependency


# Limits from Backend.md: login and registration 5 per minute per IP, resending the
# verification email once a minute, 50 offers per employer per day.
# For a live demo where the jury shares one NAT address, set RATE_LIMIT_ENABLED=false.
LoginLimit = Depends(limit_by_ip("login", 5, MINUTE))
RegisterLimit = Depends(limit_by_ip("register", 5, MINUTE))
ResendVerificationLimit = Depends(limit_by_ip("resend-verification", 1, MINUTE))
OffersPerDayLimit = Depends(limit_by_user("offers", 50, DAY))
