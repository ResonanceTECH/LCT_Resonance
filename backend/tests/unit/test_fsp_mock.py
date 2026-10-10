import pytest

from app.integrations.fsp.mock import MockFSPAdapter


@pytest.mark.asyncio
async def test_fsp_normalizer_and_history():
    adapter = MockFSPAdapter()
    member = await adapter.get_member("FSP-2026-00123")
    assert member.exists
    ach = await adapter.get_achievements("FSP-2026-00123")
    assert len(ach) == 3
    assert ach[0].external_id == "ach-001"


@pytest.mark.asyncio
async def test_fsp_no_history():
    adapter = MockFSPAdapter()
    ach = await adapter.get_achievements("FSP-2026-00999")
    assert ach == []


@pytest.mark.asyncio
async def test_find_member_by_email_or_name():
    adapter = MockFSPAdapter()
    by_email = await adapter.find_member(email="Candidate1@demo.ru", full_name=None)
    assert by_email is not None and by_email.member_id == "FSP-2026-00555"
    by_name = await adapter.find_member(email="nobody@example.com", full_name="Максим Орлов")
    assert by_name is not None and by_name.member_id == "FSP-2026-00456"
    assert await adapter.find_member(email="nobody@example.com", full_name="Нет Такого") is None
