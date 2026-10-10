"""Integration fixtures: a live Postgres from DATABASE_URL, migrated and seeded.

    uv run alembic upgrade head && uv run python -m app.seed
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
from app.models.taxonomy import Specialization


@pytest.fixture
async def client() -> AsyncIterator[AsyncClient]:
    try:
        async with SessionLocal() as db:
            await db.execute(text("SELECT 1"))
            if (await db.execute(select(Specialization.id).limit(1))).first() is None:
                pytest.skip("database is not seeded: run `python -m app.seed`")
    except (OSError, OperationalError, DBAPIError):
        pytest.skip("Postgres from DATABASE_URL is not reachable")

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    # asyncpg connections are bound to the event loop of the test that opened them.
    await engine.dispose()
