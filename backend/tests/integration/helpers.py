"""Helpers shared by integration tests (fixtures live in conftest.py)."""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from httpx import AsyncClient

API = "/api"


def unique_email(prefix: str) -> str:
    return f"{prefix}.{uuid.uuid4().hex[:10]}@example.com"


@dataclass(frozen=True)
class Account:
    id: str
    email: str
    headers: dict[str, str]


async def login(client: AsyncClient, email: str, password: str) -> Account:
    response = await client.post(f"{API}/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200, response.text
    body = response.json()
    return Account(body["user"]["id"], email, {"Authorization": f"Bearer {body['accessToken']}"})


async def register(
    client: AsyncClient,
    role: str,
    *,
    display_name: str = "Тест Тестов",
    password: str = "Passw0rd!x",
    verify: bool = True,
) -> Account:
    """Register (which signs in at once, as the frontend expects) and confirm the email
    with the dev-only token from the X-Verification-Token header."""
    email = unique_email(role)
    response = await client.post(
        f"{API}/auth/register",
        json={
            "email": email,
            "password": password,
            "role": role,
            "displayName": display_name,
            "termsAccepted": True,
            "personalDataConsent": True,
            "publicPassportConsent": False,
        },
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["user"]["emailVerified"] is False
    if verify:
        token = response.headers["X-Verification-Token"]
        verified = await client.post(f"{API}/auth/verify-email", json={"token": token})
        assert verified.json() == {"ok": True}
    return Account(body["user"]["id"], email, {"Authorization": f"Bearer {body['accessToken']}"})
