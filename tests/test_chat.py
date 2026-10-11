"""
Tests for LLM Chat Service & /api/v1/chat endpoint
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.llm_chat_service import resolve_station_code, run_chat_completion

client = TestClient(app)


def test_station_resolution():
    assert resolve_station_code("Delhi") == "NDLS"
    assert resolve_station_code("pune") == "PUNE"
    assert resolve_station_code("Mumbai") == "CSTM"
    assert resolve_station_code("gwl") == "GWL"


def test_chat_endpoint_schema():
    response = client.post("/api/v1/chat", json={
        "message": "Can I take a bus from Pune to Mumbai?",
        "conversation_history": [],
        "current_origin": "PUNE",
        "current_destination": "CSTM"
    })
    assert response.status_code == 200
    data = response.json()
    assert "reply" in data
    assert isinstance(data["reply"], str)
    assert len(data["reply"]) > 0
    assert "suggested_actions" in data
    assert isinstance(data["suggested_actions"], list)


@pytest.mark.asyncio
async def test_chat_service_completion():
    res = await run_chat_completion("Can I take a bus from Pune to Mumbai?")
    assert "reply" in res
    assert len(res["reply"]) > 0
    assert "suggested_actions" in res
