"""
Unit & Integration Tests for LLM-powered Plain Language Search (Groq Qwen 27B)
"""

import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.services.nlp_search import parse_natural_language_query, parse_natural_language_query_llm


@pytest.mark.asyncio
async def test_llm_nlp_parser_complex_query():
    """Test LLM parsing of conversational Hinglish query with constraints."""
    query = "Pune se Gwalior next week subah 11 baje se pehle pahunchna hai"
    parsed = await parse_natural_language_query_llm(query)
    assert not parsed["needs_clarification"]
    entities = parsed["extracted_entities"]
    assert entities["origin_station"] == "PUNE"
    assert entities["destination_station"] == "GWL"
    assert entities["arrive_before_time"] == "11:00"
    assert parsed["parsed_request"].origin == "PUNE"
    assert parsed["parsed_request"].destination == "GWL"


@pytest.mark.asyncio
async def test_llm_nlp_parser_ambiguous_query():
    """Test LLM correctly triggers clarification for underspecified requests."""
    query = "kuchh dino me ghar jana hai"
    parsed = await parse_natural_language_query_llm(query)
    assert parsed["needs_clarification"]
    assert parsed["clarification_message"] is not None


@pytest.mark.asyncio
async def test_llm_nlp_search_endpoint():
    """Test /api/v1/search/nlp API endpoint returns structured route results with LLM summary."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/search/nlp",
            json={"query": "Fastest route from Bangalore to Hyderabad tomorrow with bus allowed"}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["origin"] in ["SBC", "HYB", "SC"] or data["total_routes_found"] >= 0
        assert data["ai_summary"] is not None
        assert "nlp_interpretation" in data
