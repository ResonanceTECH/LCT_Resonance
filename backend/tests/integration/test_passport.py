"""Career Passport link: readable, stable across renames, public only when allowed."""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from tests.integration.helpers import API, register

pytestmark = pytest.mark.asyncio


async def _publish(client: AsyncClient, headers: dict, accepted: bool) -> None:
    response = await client.put(
        f"{API}/candidates/me/consents",
        headers=headers,
        json={"consents": [{"type": "profile_publication", "accepted": accepted}]},
    )
    assert response.status_code == 200, response.text


async def test_passport_is_published_by_consent_and_survives_a_rename(client: AsyncClient):
    cand = await register(client, "candidate", display_name="Ольга Объедкова")
    my = f"{API}/candidates/me/passport"

    link = (await client.get(my, headers=cand.headers)).json()
    assert (link["published"], link["reason"]) == (False, "CONSENT_REQUIRED")
    assert link["slug"].startswith("olga-obedkova-")
    assert link["url"].endswith(f"/p/{link['slug']}")
    assert cand.id not in link["url"]
    hidden = await client.get(f"{API}/public/passports/{link['slug']}")
    assert (hidden.status_code, hidden.json()["code"]) == (404, "PASSPORT_NOT_FOUND")

    await _publish(client, cand.headers, True)
    assert (await client.get(my, headers=cand.headers)).json()["published"] is True
    public = await client.get(f"{API}/public/passports/{link['slug']}")
    assert public.status_code == 200
    assert public.json()["publicUrl"] == link["url"]

    # The name part follows the profile, the old link keeps working.
    renamed = await client.patch(
        f"{API}/candidates/me", headers=cand.headers, json={"fullName": "Ольга Петрова"}
    )
    assert renamed.status_code == 200, renamed.text
    new_link = (await client.get(my, headers=cand.headers)).json()
    assert new_link["slug"].startswith("olga-petrova-")
    token = link["slug"].rsplit("-", 1)[1]
    assert new_link["slug"].endswith(token)
    old = await client.get(f"{API}/public/passports/{link['slug']}")
    assert old.json()["publicUrl"] == new_link["url"]

    # The internal id is not a passport address any more; withdrawal hides it at once.
    by_id = await client.get(f"{API}/public/passports/{cand.id}")
    assert by_id.status_code == 404
    await _publish(client, cand.headers, False)
    assert (await client.get(f"{API}/public/passports/{token}")).status_code == 404


async def test_unverified_email_is_reported_before_consent(client: AsyncClient):
    cand = await register(client, "candidate", verify=False)
    await _publish(client, cand.headers, True)
    link = (await client.get(f"{API}/candidates/me/passport", headers=cand.headers)).json()
    assert (link["published"], link["reason"]) == (False, "EMAIL_NOT_VERIFIED")
    hidden = await client.get(f"{API}/public/passports/{link['slug']}")
    assert hidden.status_code == 404
