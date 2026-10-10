"""Golden path (Backend.md) through the frontend contract: candidate -> test -> category ->
FSP -> employer Talent Pool -> match -> offer -> accept -> contacts."""

from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.testing import TestAttemptItem as ItemRow  # alias: pytest collects Test*
from tests.integration.helpers import API, Account, register

pytestmark = pytest.mark.asyncio

NO_HISTORY_FSP_MEMBER = "FSP-2026-00999"


async def _answer_key() -> dict[str, str]:
    """Test-only shortcut: the answer key of issued items, which the API never exposes."""
    async with SessionLocal() as db:
        rows = await db.execute(select(ItemRow.id, ItemRow.correct_option_id))
        return {str(item_id): answer for item_id, answer in rows.all()}


async def _take_test(
    client: AsyncClient, cand: Account, specialization: str, grade: str, *, correct: bool
) -> dict:
    body = {"specialization": specialization, "stack": ["Python"], "claimedGrade": grade}
    session = await client.post(f"{API}/tests/sessions", headers=cand.headers, json=body)
    assert session.status_code == 200, session.text
    session_id = session.json()["id"]
    assert session.json()["totalQuestions"] == 10
    # Starting the same test again resumes it instead of revealing new questions.
    again = await client.post(f"{API}/tests/sessions", headers=cand.headers, json=body)
    assert again.json()["id"] == session_id

    key = await _answer_key()
    for index in range(10):
        question = (
            await client.get(f"{API}/tests/sessions/{session_id}/question", headers=cand.headers)
        ).json()
        assert question["index"] == index and question["total"] == 10
        assert "correct" not in str(question).lower()
        right = key[question["id"]]
        option = (
            right if correct else next(o["id"] for o in question["options"] if o["id"] != right)
        )
        state = await client.post(
            f"{API}/tests/sessions/{session_id}/answer",
            headers=cand.headers,
            json={"questionId": question["id"], "optionId": option},
        )
        assert state.json()["currentIndex"] == index + 1
    result = await client.post(f"{API}/tests/sessions/{session_id}/finish", headers=cand.headers)
    assert result.status_code == 200, result.text
    return result.json()


async def test_golden_path_register_to_contacts(client: AsyncClient):
    cand = await register(client, "candidate", display_name="Голден Пасов")
    profile = await client.patch(
        f"{API}/candidates/me",
        headers=cand.headers,
        json={
            # What the frontend profile form sends: skills as names, blanks as "".
            "fullName": "Голден Пасов",
            "about": "",
            "specialization": "Backend",
            "claimedGrade": "middle",
            "skills": ["python", "FastAPI", "Postgres"],
            "salaryFrom": 180000,
            "salaryTo": 0,
            "currency": "RUB",
            "city": "Москва",
            "workFormat": "remote",
            "readiness": "actively_looking",
            "phone": "+79990001122",
        },
    )
    assert profile.status_code == 200, profile.text
    me = profile.json()
    assert me["skills"] == ["Python", "FastAPI", "PostgreSQL"]  # synonyms resolved
    assert (me["specialization"], me["claimedGrade"], me["salaryTo"]) == ("Backend", "middle", None)

    # FSP needs consent; a member without history is a normal 200.
    no_consent = await client.post(f"{API}/candidates/me/fsp/sync", headers=cand.headers)
    assert no_consent.json()["code"] == "CONSENT_REQUIRED"
    await client.put(
        f"{API}/candidates/me/consents",
        headers=cand.headers,
        json={"consents": [{"type": "fsp_sync", "accepted": True}]},
    )
    unknown = await client.put(
        f"{API}/candidates/me/fsp/link", headers=cand.headers, json={"fspMemberId": "FSP-NOPE-1"}
    )
    assert unknown.json()["code"] == "FSP_MEMBER_NOT_FOUND"
    linked = await client.put(
        f"{API}/candidates/me/fsp/link",
        headers=cand.headers,
        json={"fspMemberId": NO_HISTORY_FSP_MEMBER},
    )
    try:
        assert linked.status_code == 200, linked.text
        sync = await client.post(f"{API}/candidates/me/fsp/sync", headers=cand.headers)
        assert (sync.json()["status"], sync.json()["achievements"]) == ("no_history", [])

        result = await _take_test(client, cand, "Backend", "middle", correct=True)
        assert (result["score"], result["gradeConfirmed"]) == (100, True)
        me = (await client.get(f"{API}/candidates/me", headers=cand.headers)).json()
        assert me["confirmedGrade"] == "middle" and me["testResult"]["score"] == 100

        # Employer: vacancy (the company is created from companyName), Talent Pool.
        emp = await register(client, "employer", display_name="Игорь Тестов")
        vacancy = await client.post(
            f"{API}/employer/vacancies",
            headers=emp.headers,
            json={
                "companyName": "GP Co",
                "title": "Backend Developer",
                "description": "API",
                "specialization": "Backend",
                "requiredGrade": "middle",
                "requiredSkills": ["Python", "FastAPI"],
                "niceToHaveSkills": ["Docker"],
                "salaryFrom": 200000,
                "salaryTo": 280000,
                "currency": "RUB",
                "workFormat": "remote",
                "status": "active",
            },
        )
        assert vacancy.status_code == 201, vacancy.text
        vacancy_id = vacancy.json()["id"]
        pool = await client.get(
            f"{API}/candidates", headers=emp.headers, params={"vacancyId": vacancy_id, "limit": 50}
        )
        assert pool.status_code == 200, pool.text
        item = next(i for i in pool.json()["items"] if i["id"] == cand.id)
        match = item["match"]
        assert match["matchedSkills"] == ["Python", "FastAPI"]
        assert match["missingInProfileSkills"] == ["Docker"]
        assert {
            "code": "GRADE_CONFIRMED",
            "label": "грейд middle подтверждён тестом",
            "positive": True,
        } in match["reasons"]
        assert "phone" not in item  # contacts never in the Talent Pool

        # Offer -> contacts locked -> candidate opens (viewed) -> accept -> contacts.
        offer = await client.post(
            f"{API}/offers",
            headers=emp.headers,
            json={
                "vacancyId": vacancy_id,
                "candidateId": cand.id,
                "companyName": "GP Co",
                "positionTitle": "Backend Developer",
                "salaryFrom": 220000,
                "salaryTo": 280000,
                "currency": "RUB",
                "workFormat": "remote",
                "message": "Готовы обсудить старт",
            },
        )
        assert offer.status_code == 201, offer.text
        offer_id = offer.json()["id"]
        assert offer.json()["employerContact"] == {"type": "email", "value": emp.email}
        locked = await client.get(f"{API}/candidates/{cand.id}/contacts", headers=emp.headers)
        assert (locked.status_code, locked.json()["code"]) == (403, "CONTACTS_LOCKED")

        inbox = (await client.get(f"{API}/candidate/offers", headers=cand.headers)).json()
        assert [o["status"] for o in inbox] == ["new"]
        opened = await client.get(f"{API}/offers/{offer_id}", headers=cand.headers)
        assert opened.json()["status"] == "viewed"
        accepted = await client.post(f"{API}/offers/{offer_id}/accept", headers=cand.headers)
        assert accepted.json()["status"] == "accepted"
        twice = await client.post(f"{API}/offers/{offer_id}/decline", headers=cand.headers)
        assert twice.json()["code"] == "INVALID_OFFER_STATE"

        contacts = await client.get(f"{API}/candidates/{cand.id}/contacts", headers=emp.headers)
        assert contacts.json() == {"email": cand.email, "phone": "+79990001122", "telegram": None}
        notes = (await client.get(f"{API}/notifications", headers=emp.headers)).json()
        assert notes["unread"] >= 1 and notes["items"][0]["type"] == "offer_accepted"
    finally:
        # FSP member ids are unique across accounts: free it for the next run.
        await client.delete(f"{API}/candidates/me/fsp/link", headers=cand.headers)


async def test_failed_test_pauses_same_grade_but_not_lower(client: AsyncClient):
    cand = await register(client, "candidate")
    failed = await _take_test(client, cand, "Backend", "middle", correct=False)
    assert failed["gradeConfirmed"] is False and failed["retryAvailableAt"]

    body = {"specialization": "Backend", "stack": [], "claimedGrade": "middle"}
    retry = await client.post(f"{API}/tests/sessions", headers=cand.headers, json=body)
    assert retry.json()["code"] == "TEST_RETRY_COOLDOWN"
    lower = await client.post(
        f"{API}/tests/sessions", headers=cand.headers, json={**body, "claimedGrade": "junior"}
    )
    # Not blocked by the pause; the demo bank simply has no junior questions.
    assert lower.json()["code"] == "TEST_BANK_INSUFFICIENT"
    history = (await client.get(f"{API}/tests/history", headers=cand.headers)).json()
    assert history[0]["specialization"] == "Backend"


async def test_withdrawing_publication_consent_hides_profile(client: AsyncClient):
    cand = await register(client, "candidate")
    emp = await register(client, "employer")
    url = f"{API}/candidates/{cand.id}"
    assert (await client.get(url, headers=emp.headers)).status_code == 200

    async def publish(accepted: bool) -> None:
        response = await client.put(
            f"{API}/candidates/me/consents",
            headers=cand.headers,
            json={"consents": [{"type": "profile_publication", "accepted": accepted}]},
        )
        assert response.status_code == 200, response.text

    await publish(False)
    assert (await client.get(url, headers=emp.headers)).status_code == 404
    await publish(True)
    assert (await client.get(url, headers=emp.headers)).status_code == 200


async def test_business_rules_return_clear_errors(client: AsyncClient):
    unverified = await register(client, "employer", verify=False)
    cand = await register(client, "candidate")
    offer = {
        "candidateId": cand.id,
        "positionTitle": "Dev",
        "message": "Привет",
        "salaryFrom": 100000,
        "salaryTo": 200000,
    }
    blocked = await client.post(f"{API}/offers", headers=unverified.headers, json=offer)
    assert (blocked.status_code, blocked.json()["code"]) == (403, "EMAIL_NOT_VERIFIED")

    emp = await register(client, "employer")
    usd = await client.post(f"{API}/offers", headers=emp.headers, json={**offer, "currency": "USD"})
    assert (usd.status_code, usd.json()["code"]) == (422, "CURRENCY_NOT_SUPPORTED")
    inverted = await client.post(
        f"{API}/offers", headers=emp.headers, json={**offer, "salaryFrom": 300000}
    )
    assert inverted.json()["code"] == "INVALID_SALARY_RANGE"
    unknown = await client.post(
        f"{API}/employer/vacancies",
        headers=emp.headers,
        json={
            "title": "T",
            "description": "D",
            "specialization": "Cobol",
            "requiredGrade": "middle",
            "salaryFrom": 1,
            "salaryTo": 2,
        },
    )
    assert unknown.json()["code"] == "UNKNOWN_SPECIALIZATION"
    wrong_role = await client.get(f"{API}/candidates", headers=cand.headers)
    assert (wrong_role.status_code, wrong_role.json()["code"]) == (403, "FORBIDDEN_ROLE")
