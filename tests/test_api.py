"""
Integration tests for FastAPI endpoints using TestClient.
"""

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_root_health():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "MargDarshak"
    assert data["status"] == "running"


def test_api_health():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


def test_search_stations_autocomplete():
    response = client.get("/api/v1/stations/search?q=Gwal")
    assert response.status_code == 200
    results = response.json()
    assert isinstance(results, list)
    assert any(s["code"] == "GWL" for s in results)


def test_route_search_endpoint():
    payload = {
        "origin": "GWL",
        "destination": "PUNE",
        "travel_date": "2025-01-15",
        "max_transfers": 2,
        "priority": "balanced",
    }
    response = client.post("/api/v1/search", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["origin"] == "GWL"
    assert data["destination"] == "PUNE"
    assert data["total_routes_found"] > 0
    assert len(data["routes"]) > 0

    first_route = data["routes"][0]
    assert "label" in first_route
    assert "total_travel_time" in first_route
    assert "transfers" in first_route
    assert len(first_route["legs"]) > 0


def test_train_live_status():
    response = client.get("/api/v1/trains/12627/live")
    assert response.status_code == 200
    data = response.json()
    assert data["train_number"] == "12627"
    assert "delay_minutes" in data
