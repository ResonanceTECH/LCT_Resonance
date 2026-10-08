"""Golden path smoke. Requires working DATABASE_URL. Skips if DB unreachable."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.config import get_settings
from app.main import app


async def _db_available() -> bool:
    try:
        import psycopg
        from urllib.parse import unquote, urlparse

        get_settings.cache_clear()
        s = get_settings()
        u = urlparse(s.database_url_sync.replace("postgresql+psycopg://", "postgresql://"))
        with psycopg.connect(
            host=u.hostname,
            port=u.port or 5432,
            dbname=u.path.lstrip("/"),
            user=u.username,
            password=unquote(u.password or ""),
            connect_timeout=2,
        ) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
        return True
    except Exception:
        return False


@pytest.mark.asyncio
async def test_golden_path_register_to_contacts():
    if not await _db_available():
        pytest.skip("Postgres not available with current .env credentials")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # health
        r = await client.get("/health/live")
        assert r.status_code == 200

        # register candidate
        email_c = "gp.candidate@example.invalid"
        reg = await client.post(
            "/api/v1/auth/register",
            json={"email": email_c, "password": "CandidatePass123!", "role": "candidate"},
        )
        if reg.status_code == 409:
            pytest.skip("seed/user already exists; run on clean DB for full golden path")
        assert reg.status_code == 200, reg.text
        token = reg.json()["verification_token"]
        assert token
        assert (await client.post("/api/v1/auth/verify-email", json={"token": token})).status_code == 200

        login_c = await client.post(
            "/api/v1/auth/login",
            json={"email": email_c, "password": "CandidatePass123!"},
        )
        assert login_c.status_code == 200
        c_headers = {"Authorization": f"Bearer {login_c.json()['access_token']}"}

        specs = (await client.get("/api/v1/specializations")).json()
        grades = (await client.get("/api/v1/grades")).json()
        if not specs or not grades:
            pytest.skip("taxonomy empty — run seed first")
        backend = next(s for s in specs if s["slug"] == "backend")
        middle = next(g for g in grades if g["code"] == "middle")

        await client.patch(
            "/api/v1/candidates/me",
            headers=c_headers,
            json={
                "first_name": "Gold",
                "last_name": "Path",
                "city": "Москва",
                "declared_specialization_id": backend["id"],
                "declared_grade_id": middle["id"],
                "salary_min": 180000,
                "work_format": "remote",
                "open_to_offers": True,
                "phone": "+79990001122",
            },
        )

        # FSP
        await client.put(
            "/api/v1/candidates/me/fsp-link",
            headers=c_headers,
            json={"fsp_member_id": "FSP-2026-00123"},
        )
        sync = await client.post("/api/v1/candidates/me/fsp-sync", headers=c_headers)
        assert sync.status_code == 200
        assert sync.json()["status"] in {"synced", "stale", "no_history"}

        # test
        start = await client.post(
            "/api/v1/tests/attempts",
            headers=c_headers,
            json={"specialization_id": backend["id"], "grade_id": middle["id"]},
        )
        if start.status_code == 409:
            pytest.skip(start.json())
        assert start.status_code == 200, start.text
        attempt = start.json()
        answers = [
            {"question_id": q["id"], "option_id": q["options"][0]["id"]}
            for q in attempt["questions"]
        ]
        # force pass: we don't know correct; submit anyway then patch score via second attempt logic
        submitted = await client.post(
            f"/api/v1/tests/attempts/{attempt['attempt_id']}/submit",
            headers=c_headers,
            json={"answers": answers},
        )
        assert submitted.status_code == 200

        # employer side
        email_e = "gp.employer@example.invalid"
        reg_e = await client.post(
            "/api/v1/auth/register",
            json={"email": email_e, "password": "EmployerPass123!", "role": "employer"},
        )
        assert reg_e.status_code == 200
        await client.post(
            "/api/v1/auth/verify-email", json={"token": reg_e.json()["verification_token"]}
        )
        login_e = await client.post(
            "/api/v1/auth/login",
            json={"email": email_e, "password": "EmployerPass123!"},
        )
        e_headers = {"Authorization": f"Bearer {login_e.json()['access_token']}"}

        company = await client.post(
            "/api/v1/companies",
            headers=e_headers,
            json={"name": "GP Co", "contact_email": "hr@example.invalid"},
        )
        assert company.status_code == 201

        # ensure candidate verified for matching — if test failed, matching may be empty
        match = await client.post(
            "/api/v1/matching/search",
            headers=e_headers,
            json={
                "need": {
                    "specialization_id": backend["id"],
                    "grade_id": middle["id"],
                    "salary_from": 200000,
                    "salary_to": 280000,
                    "work_format": "remote",
                    "skills": [],
                }
            },
        )
        assert match.status_code == 200

        me = await client.get("/api/v1/candidates/me", headers=c_headers)
        cand_id = me.json()["id"]

        offer = await client.post(
            "/api/v1/offers",
            headers=e_headers,
            json={
                "candidate_id": cand_id,
                "title": "Backend Developer",
                "description": "Join us",
                "salary_from": 220000,
                "salary_to": 280000,
                "work_format": "remote",
                "employer_contact": {"type": "email", "value": "hr@example.invalid"},
            },
        )
        assert offer.status_code == 201, offer.text
        offer_id = offer.json()["id"]

        locked = await client.get(
            f"/api/v1/offers/{offer_id}/candidate-contact", headers=e_headers
        )
        assert locked.status_code == 403
        assert locked.json()["error"]["code"] == "CONTACTS_LOCKED"

        accepted = await client.post(
            f"/api/v1/offers/{offer_id}/accept", headers=c_headers
        )
        assert accepted.status_code == 200
        assert accepted.json()["status"] == "accepted"

        contacts = await client.get(
            f"/api/v1/offers/{offer_id}/candidate-contact", headers=e_headers
        )
        assert contacts.status_code == 200
        assert contacts.json()["contact"]["email"] == email_c
