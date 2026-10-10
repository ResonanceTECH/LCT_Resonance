import pytest
from httpx import ASGITransport, AsyncClient

from app.core.config import get_settings
from app.core.rate_limit import SlidingWindowLimiter, limiter
from app.main import app


class FakeClock:
    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now


def test_sliding_window_blocks_and_recovers():
    clock = FakeClock()
    rl = SlidingWindowLimiter(clock)
    assert [rl.hit("k", limit=2, window_sec=60) for _ in range(2)] == [None, None]
    assert rl.hit("k", limit=2, window_sec=60) == pytest.approx(60)
    assert rl.hit("other", limit=2, window_sec=60) is None  # keys are independent
    clock.now += 61
    assert rl.hit("k", limit=2, window_sec=60) is None


@pytest.fixture
def limits_on(monkeypatch):
    monkeypatch.setattr(get_settings(), "rate_limit_enabled", True)
    limiter.reset()
    yield
    limiter.reset()


@pytest.mark.asyncio
async def test_registration_is_limited_per_ip(limits_on):
    # The limiter runs before body validation, so an invalid body needs no database.
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as client:
        statuses = [
            (await client.post("/api/auth/register", json={})).status_code for _ in range(6)
        ]
        limited = await client.post("/api/auth/register", json={})
    assert statuses == [422] * 5 + [429]
    assert limited.json()["code"] == "RATE_LIMITED"
    assert limited.json()["message"].startswith("Слишком много запросов")
    assert int(limited.headers["Retry-After"]) >= 1
