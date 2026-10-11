"""Integration fixtures: a live Postgres from DATABASE_URL, migrated and seeded with demo data.

    uv run alembic upgrade head && uv run python -m app.seed --demo
    uv run pytest tests/integration -q

Tests skip (not fail) when the database is unreachable or not seeded.
"""

from __future__ import annotations

from collections.abc import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select, text
from sqlalchemy.exc import DBAPIError, OperationalError

from app.db.session import SessionLocal, engine
from app.main import app
from app.models.user import User
from app.seed.data import DEMO_ADMIN_EMAIL


@pytest.fixture
async def client() -> AsyncIterator[AsyncClient]:
    try:
        async with SessionLocal() as db:
            await db.execute(text("SELECT 1"))
            demo_admin = select(User.id).where(User.email == DEMO_ADMIN_EMAIL)
            if (await db.execute(demo_admin)).first() is None:
                pytest.skip("no demo data: run `python -m app.seed --demo`")
    except (OSError, OperationalError, DBAPIError):
        pytest.skip("Postgres from DATABASE_URL is not reachable")

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    # asyncpg connections are bound to the event loop of the test that opened them.
    await engine.dispose()
