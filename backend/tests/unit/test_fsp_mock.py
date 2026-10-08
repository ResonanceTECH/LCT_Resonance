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
