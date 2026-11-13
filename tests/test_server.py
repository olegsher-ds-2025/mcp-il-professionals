import asyncio

import pytest
from fastmcp import Client

from mcp_il_professionals import server

FAKE = {"total": 1, "records": [{"dummy": "value"}]}


async def _fake_search(resource_id, **kwargs):
    return FAKE


def _call(tool, args):
    async def run():
        async with Client(server.mcp) as client:
            return await client.call_tool(tool, args)

    return asyncio.run(run())


def test_tools_registered():
    async def run():
        async with Client(server.mcp) as client:
            return {t.name for t in await client.list_tools()}

    names = asyncio.run(run())
    assert {'verify_professional', 'contractor_profile', 'find_contractors', 'search_all_registries', 'health', 'list_professions'} <= names


def test_offline_call_has_provenance(monkeypatch):
    monkeypatch.setattr(server, "datastore_search", _fake_search)
    result = _call('verify_professional', {'profession': 'cpa', 'name': 'כהן'})
    data = result.data if hasattr(result, "data") else result
    assert "source" in data and "data.gov.il" in data["source"]


def test_clean_value():
    from mcp_il_professionals.ckan import clean_value

    assert clean_value("בע~מ") == 'בע"מ'
    assert clean_value("  ") is None


@pytest.mark.live
def test_live_smoke():
    result = _call('find_contractors', {'city': 'מודיעין', 'branch': 'שיפוצים', 'limit': 2})
    data = result.data if hasattr(result, "data") else result
    assert "retrieved_at" in data
