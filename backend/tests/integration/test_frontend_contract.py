"""Contract check against the frontend types (Backend.md, "Контрактная проверка").

Required fields of each type in frontend/src/entities/types.ts must be present in the real
API response, so a renamed or dropped field is caught before the demo, not during it.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from httpx import AsyncClient

from app.seed.data import DEMO_PASSWORD
from tests.integration.helpers import API, login, register

pytestmark = pytest.mark.asyncio

TYPES_FILE = Path(__file__).resolve().parents[3] / "frontend" / "src" / "entities" / "types.ts"
_TYPE_START = re.compile(r"export type (\w+) =([^{;]*)\{")
_FIELD = re.compile(r"^\s*(\w+)(\?)?:")


def _required_fields() -> dict[str, set[str]]:
    """Top-level required fields per exported object type (intersections included)."""
    source = TYPES_FILE.read_text(encoding="utf-8")
    types: dict[str, set[str]] = {}
    for match in _TYPE_START.finditer(source):
        name, prefix = match.group(1), match.group(2)
        depth, body_start = 1, match.end()
        index = body_start
        while depth:
            depth += {"{": 1, "}": -1}.get(source[index], 0)
            index += 1
        fields: set[str] = set()
        depth = 0
        for line in source[body_start : index - 1].splitlines():
            field = _FIELD.match(line)
            if depth == 0 and field and not field.group(2):
                fields.add(field.group(1))
            depth += line.count("{") - line.count("}")
        # `A & { ... }`: inherit the required fields of A.
        for base in re.findall(r"(\w+)\s*&", prefix):
            fields |= types.get(base, set())
        types[name] = fields
    return types


@pytest.fixture(scope="module")
def frontend_types() -> dict[str, set[str]]:
    if not TYPES_FILE.exists():
        pytest.skip("frontend sources are not next to the backend")
    return _required_fields()


def _check(types: dict[str, set[str]], type_name: str, payload: dict) -> None:
    missing = types[type_name] - set(payload)
    assert not missing, f"{type_name}: missing {sorted(missing)}"


async def test_responses_carry_every_required_frontend_field(
    client: AsyncClient, frontend_types: dict[str, set[str]]
):
    t = frontend_types
    cand = await login(client, "candidate@demo.ru", DEMO_PASSWORD)
    emp = await login(client, "employer@demo.ru", DEMO_PASSWORD)
    admin = await login(client, "admin@demo.ru", DEMO_PASSWORD)

    async def get(account, path: str, **params):
        response = await client.get(f"{API}{path}", headers=account.headers, params=params)
        assert response.status_code == 200, (path, response.text)
        return response.json()

    _check(t, "AuthUser", await get(cand, "/auth/me"))
    me = await get(cand, "/candidates/me")
    _check(t, "CandidateProfile", me)
    _check(t, "TestResultSummary", me["testResult"])
    _check(t, "ProfileCompleteness", await get(cand, "/candidates/me/completeness"))
    fsp = await get(cand, "/candidates/me/fsp/achievements")
    _check(t, "FspAchievementsResponse", fsp)
    _check(t, "FspAchievement", fsp["achievements"][0])
    _check(t, "TestHistoryItem", (await get(cand, "/tests/history"))[0])
    _check(t, "CandidateDashboard", await get(cand, "/dashboard/candidate"))
    catalog = await get(cand, "/vacancies", matchToMe="true")
    _check(t, "VacancyWithMatch", catalog[0])
    _check(t, "CandidateMatch", catalog[0]["match"])
    _check(t, "Offer", (await get(cand, "/candidate/offers"))[0])
    notifications = await get(cand, "/notifications")
    _check(t, "AppNotification", notifications["items"][0])
    passport = await get(cand, "/candidates/me/passport")
    _check(t, "CandidatePassport", passport)
    _check(t, "PublicPassport", await get(cand, f"/public/passports/{passport['slug']}"))

    vacancy = (await get(emp, "/employer/vacancies"))[0]
    _check(t, "Vacancy", vacancy)
    pool = await get(emp, "/candidates", vacancyId=vacancy["id"])
    _check(t, "TalentPoolResponse", pool)
    _check(t, "TalentPoolItem", pool["items"][0])
    _check(t, "CandidateMatch", pool["items"][0]["match"])
    _check(t, "MatchReason", pool["items"][0]["match"]["reasons"][0])
    _check(t, "SkillRadar", await get(emp, f"/candidates/{me['id']}/skill-radar"))
    shortlist = await get(emp, "/employer/shortlist")
    _check(
        t,
        "CandidateCompareResponse",
        await get(emp, "/employer/candidates/compare", ids=",".join(c["id"] for c in shortlist)),
    )
    _check(t, "EmployerDashboard", await get(emp, "/dashboard/employer"))
    _check(t, "EmployerAnalytics", await get(emp, "/dashboard/employer/analytics"))

    _check(t, "AdminOverview", await get(admin, "/admin/overview"))
    _check(t, "AdminUserRow", (await get(admin, "/admin/users"))[0])


async def test_auth_and_testing_shapes(client: AsyncClient, frontend_types: dict[str, set[str]]):
    t = frontend_types
    response = await client.post(
        f"{API}/auth/login", json={"email": "candidate@demo.ru", "password": DEMO_PASSWORD}
    )
    _check(t, "AuthResponse", response.json())

    cand = await register(client, "candidate")
    session = await client.post(
        f"{API}/tests/sessions",
        headers=cand.headers,
        json={"specialization": "Backend", "stack": ["Python"], "claimedGrade": "middle"},
    )
    _check(t, "TestSession", session.json())
    question = await client.get(
        f"{API}/tests/sessions/{session.json()['id']}/question", headers=cand.headers
    )
    _check(t, "TestQuestion", question.json())
