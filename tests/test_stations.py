"""Unit and integration tests for IRCTC station search and popular stations."""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.station_service import search_stations, get_popular_stations

client = TestClient(app)


@pytest.mark.asyncio
async def test_search_by_code():
    results = await search_stations("GWL", limit=5)
    assert len(results) > 0
    assert results[0].code == "GWL"
    assert "GWALIOR" in results[0].name.upper()


@pytest.mark.asyncio
async def test_search_by_name():
    results = await search_stations("Gwalior", limit=5)
    assert any(r.code == "GWL" for r in results)


@pytest.mark.asyncio
async def test_search_by_city_hub():
    results = await search_stations("Delhi", limit=10)
    codes = [r.code for r in results]
    assert "NDLS" in codes or "NZM" in codes or "DLI" in codes


@pytest.mark.asyncio
async def test_search_satellite_city():
    results = await search_stations("Noida", limit=5)
    assert len(results) > 0
    assert any(r.distance_km is not None and r.distance_km > 0 for r in results)
    assert any(r.code in ("ANVT", "NZM", "NDLS", "GZB") for r in results)


def test_popular_stations():
    pop = get_popular_stations()
    assert len(pop) >= 8
    pop_codes = [p.code for p in pop]
    assert "NDLS" in pop_codes
    assert "GWL" in pop_codes
    assert "PUNE" in pop_codes


def test_api_stations_search_endpoint():
    response = client.get("/api/v1/stations/search?q=GWL")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert data[0]["code"] == "GWL"


def test_api_stations_popular_endpoint():
    response = client.get("/api/v1/stations/popular")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 8
    codes = [item["code"] for item in data]
    assert "NDLS" in codes
