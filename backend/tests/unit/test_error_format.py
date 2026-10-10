"""Error envelope checks that need no database: validation fails before any query."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


def _client() -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://t")


@pytest.mark.asyncio
async def test_validation_error_is_flat_russian_and_does_not_echo_input():
    async with _client() as client:
        response = await client.post(
            "/api/auth/register",
            json={
                "email": "a@example.com",
                "password": "sekret7",
                "role": "candidate",
                "displayName": "Аня",
            },
            headers={"X-Request-Id": "test-req-1"},
        )
    assert response.status_code == 422
    assert response.headers["X-Request-Id"] == "test-req-1"
    body = response.json()
    # The frontend shows `message` as is.
    assert body["message"] == "password: слишком короткое значение (минимум 8)"
    assert body["code"] == "VALIDATION_ERROR"
    assert body["requestId"] == "test-req-1"
    assert "sekret7" not in response.text  # a too-short password must not be echoed
    assert all(set(f) == {"field", "message", "type"} for f in body["details"]["fields"])


@pytest.mark.asyncio
async def test_business_codes_from_validators():
    async with _client() as client:
        response = await client.post(
            "/api/auth/register",
            json={
                "email": "not-an-email",
                "password": "12345678",
                "role": "candidate",
                "displayName": "Аня",
            },
        )
    assert response.json()["message"] == "email: некорректный email"


@pytest.mark.asyncio
async def test_unauthenticated_request_gets_401_message():
    async with _client() as client:
        response = await client.get("/api/auth/me")
    assert response.status_code == 401
    assert response.json() == {
        "message": "Требуется авторизация",
        "code": "UNAUTHORIZED",
        "details": {},
        "requestId": response.headers["X-Request-Id"],
    }


@pytest.mark.asyncio
async def test_unknown_route_is_a_404_in_the_same_format():
    async with _client() as client:
        response = await client.get("/api/nope")
    assert response.status_code == 404
    assert response.json()["message"] == "Не найдено"


@pytest.mark.asyncio
async def test_malformed_request_id_is_replaced():
    async with _client() as client:
        response = await client.get("/api/health/live", headers={"X-Request-Id": "bad id <script>"})
    assert response.headers["X-Request-Id"].startswith("req_")
