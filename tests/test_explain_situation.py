"""Tests for explain_situation tool."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from indian_legal_mcp_server.src.tools.explain_situation import (
    explain_situation,
    classify_scenario,
)
from indian_legal_mcp_server.services.statute_index import build_index_from_json


@pytest.fixture(autouse=True)
def setup_index():
    build_index_from_json(
        "indian_legal_mcp_server/data/statutes",
        "indian_legal_mcp_server/data/statute_index.db",
    )
    yield


def test_classify_arrest():
    result = classify_scenario("My brother was arrested by police without any reason")
    assert result["primary_domain"] == "criminal"
    assert result["sub_domain"] == "arrest_and_bail"


def test_classify_maintenance():
    result = classify_scenario(
        "My husband is not paying maintenance for me and my child"
    )
    assert result["primary_domain"] == "family"
    assert result["sub_domain"] == "maintenance"


def test_classify_divorce():
    result = classify_scenario("I want a divorce from my husband due to cruelty")
    assert result["primary_domain"] == "family"
    assert result["sub_domain"] == "divorce"


def test_classify_cheque_bounce():
    result = classify_scenario("A cheque of Rs 5 lakh was dishonoured")
    assert result["primary_domain"] == "commercial"
    assert result["sub_domain"] == "cheque_bounce"


@pytest.mark.asyncio
async def test_explain_situation_basic():
    result = await explain_situation(
        scenario="My husband has been harassing me for dowry. He beats me. What are my options?",
        detail_level="brief",
    )
    assert result["status"] == "success"
    assert "classification" in result
