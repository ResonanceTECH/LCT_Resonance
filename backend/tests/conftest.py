"""Shared test setup.

Unit tests must run without a database or a local `.env`. When `backend/.env` is absent,
placeholder settings are injected; they are never used to connect anywhere in unit tests.
"""

from __future__ import annotations

import os
from pathlib import Path

_ENV_FILE = Path(__file__).resolve().parents[1] / ".env"
_UNIT_TEST_DEFAULTS = {
    "DATABASE_URL": "postgresql+asyncpg://postgres@localhost:5432/resonance_test",
    "DATABASE_URL_SYNC": "postgresql+psycopg://postgres@localhost:5432/resonance_test",
    "JWT_SECRET": "unit-test-secret-unit-test-secret-0123",
    "APP_ENV": "test",
}

if not _ENV_FILE.exists():
    for key, value in _UNIT_TEST_DEFAULTS.items():
        os.environ.setdefault(key, value)

# Tests log in and register far more often than 5 times a minute from one address.
# The limiter itself is covered by tests/unit/test_rate_limit.py.
os.environ.setdefault("RATE_LIMIT_ENABLED", "false")

# Never send real mail from tests, even when the local .env has a working SMTP account:
# every registration would email a fake address from it. tests/unit/test_email.py covers
# the SMTP path with a stub.
os.environ["SMTP_HOST"] = ""
