"""Tests for statute_search tool."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from indian_legal_mcp_server.src.tools._impl.statute_search import statute_search
from indian_legal_mcp_server.services.statute_index import build_index_from_json


@pytest.fixture(autouse=True)
def setup_index():
    """Build test index before running tests."""
    build_index_from_json(
        "indian_legal_mcp_server/data/statutes",
        "indian_legal_mcp_server/data/statute_index.db",
    )
    yield


@pytest.mark.asyncio
async def test_search_by_section():
    result = await statute_search(query="section 103")
    assert result["status"] == "success"
    assert result["total_results"] > 0


@pytest.mark.asyncio
async def test_search_bns():
    result = await statute_search(query="murder punishment", act_filter="bns_2023")
    assert result["status"] == "success"


@pytest.mark.asyncio
async def test_search_maintenance():
    result = await statute_search(query="maintenance wife child")
    assert result["status"] == "success"


@pytest.mark.asyncio
async def test_search_no_results():
    result = await statute_search(query="zzzznonexistent")
    assert result["status"] == "success"
    assert result["total_results"] == 0


@pytest.mark.asyncio
async def test_search_act_filter():
    result = await statute_search(query="divorce", act_filter="hma_1955")
    assert result["status"] == "success"
