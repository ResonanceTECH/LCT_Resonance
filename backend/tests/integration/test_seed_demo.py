"""The seeded demo must work as advertised in README: logins, the A/B ranking pair,
automatic FSP linking and the employer screens."""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.seed.data import DEMO_PASSWORD
from tests.integration.helpers import API, login

pytestmark = pytest.mark.asyncio


@pytest.mark.parametrize(
    ("email", "role", "name"),
    [
        ("admin@demo.ru", "admin", "Админ Resonance"),
        ("employer@demo.ru", "employer", "Игорь Смирнов"),
        ("candidate@demo.ru", "candidate", "Анна Ковалёва"),
    ],
)
async def test_frontend_demo_accounts_work(client: AsyncClient, email: str, role: str, name: str):
    account = await login(client, email, DEMO_PASSWORD)
    me = (await client.get(f"{API}/auth/me", headers=account.headers)).json()
    assert (me["email"], me["role"], me["displayName"]) == (email, role, name)


async def test_ranking_uses_several_signals(client: AsyncClient):
    employer = await login(client, "employer@demo.ru", DEMO_PASSWORD)
    vacancies = (await client.get(f"{API}/employer/vacancies", headers=employer.headers)).json()
    react = next(v for v in vacancies if v["title"] == "Frontend Engineer (React)")

    pool = await client.get(
        f"{API}/candidates", headers=employer.headers, params={"vacancyId": react["id"]}
    )
    items = pool.json()["items"]
    names = [item["fullName"] for item in items]
    # Анна (test 82, full stack, FSP, remote) outranks Елена (test 91, office, no FSP).
    assert names.index("Анна Ковалёва") < names.index("Елена Ветрова")
    elena = items[names.index("Елена Ветрова")]
    assert any(not reason["positive"] for reason in elena["match"]["reasons"])


async def test_fsp_sync_finds_registry_member_by_email(client: AsyncClient):
    """candidate1 is seeded unlinked; the mock registry knows the account email."""
    candidate = await login(client, "candidate1@demo.ru", DEMO_PASSWORD)
    sync = await client.post(f"{API}/candidates/me/fsp/sync", headers=candidate.headers)
    assert sync.status_code == 200, sync.text
    body = sync.json()
    assert body["status"] == "synced" and len(body["achievements"]) == 1
    assert body["achievements"][0]["sportRank"] == "2 разряд"


async def test_employer_screens_have_data(client: AsyncClient):
    employer = await login(client, "employer@demo.ru", DEMO_PASSWORD)
    dashboard = (await client.get(f"{API}/dashboard/employer", headers=employer.headers)).json()
    assert dashboard["shortlistSize"] == 2 and dashboard["offersSent"] >= 4
    analytics = (
        await client.get(f"{API}/dashboard/employer/analytics", headers=employer.headers)
    ).json()
    assert analytics["topSkills"] and analytics["avgMatchScore"] is not None
    shortlist = (await client.get(f"{API}/employer/shortlist", headers=employer.headers)).json()
    ids = ",".join(c["id"] for c in shortlist)
    compare = await client.get(
        f"{API}/employer/candidates/compare", headers=employer.headers, params={"ids": ids}
    )
    assert len(compare.json()["radars"]) == 2


async def test_public_passport_needs_no_login(client: AsyncClient):
    candidate = await login(client, "candidate@demo.ru", DEMO_PASSWORD)
    link = (await client.get(f"{API}/candidates/me/passport", headers=candidate.headers)).json()
    assert link["published"] is True
    assert link["slug"].startswith("anna-kovaleva-")
    passport = await client.get(f"{API}/public/passports/{link['slug']}")
    assert passport.status_code == 200
    assert passport.json()["profile"]["fullName"] == "Анна Ковалёва"
    assert passport.json()["publicUrl"] == link["url"]
    assert "phone" not in passport.json()["profile"]
