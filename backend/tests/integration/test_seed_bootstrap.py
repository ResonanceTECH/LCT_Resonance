"""`python -m app.seed` on a stand without demo data: reference data plus the admin from env."""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.core.config import get_settings
from app.seed.__main__ import seed
from tests.integration.helpers import API, login, register, unique_email

pytestmark = pytest.mark.asyncio

PASSWORD = "Adm1n-Passw0rd"


async def _seed_admin(monkeypatch, capsys, email: str, password: str) -> str:
    settings = get_settings()
    monkeypatch.setattr(settings, "admin_email", email)
    monkeypatch.setattr(settings, "admin_password", password)
    await seed()
    return capsys.readouterr().out


async def test_admin_from_env_is_created_once_and_can_log_in(
    client: AsyncClient, monkeypatch, capsys
):
    email = unique_email("admin")
    first = await _seed_admin(monkeypatch, capsys, f"  {email.upper()} ", PASSWORD)
    assert f"SEED admin: {email} created" in first
    assert "SEED reference: exists" in first
    assert "SEED demo: off" in first

    again = await _seed_admin(monkeypatch, capsys, email, "another-password")
    assert f"SEED admin: {email} exists" in again

    admin = await login(client, email, PASSWORD)
    me = (await client.get(f"{API}/auth/me", headers=admin.headers)).json()
    assert (me["role"], me["emailVerified"]) == ("admin", True)
    overview = await client.get(f"{API}/admin/overview", headers=admin.headers)
    assert overview.status_code == 200


async def test_weak_password_or_foreign_account_never_becomes_admin(
    client: AsyncClient, monkeypatch, capsys
):
    weak = await _seed_admin(monkeypatch, capsys, unique_email("admin"), "short")
    assert "WARNING: not created" in weak

    employer = await register(client, "employer")
    taken = await _seed_admin(monkeypatch, capsys, employer.email, PASSWORD)
    assert "WARNING" in taken and "employer" in taken
    me = (await client.get(f"{API}/auth/me", headers=employer.headers)).json()
    assert me["role"] == "employer"
