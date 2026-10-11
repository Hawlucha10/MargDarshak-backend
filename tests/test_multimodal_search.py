"""
Tests for Unified Multimodal Search (RAPTOR + Bus Bridging)
Verifies:
- Direct bus route discovery
- Intermodal transfers (Train -> Bus and Bus -> Train)
- Train + Bus multi-hop journeys
"""

import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.schemas.route import RouteSearchRequest
from app.api.v1.search import search_routes


@pytest.mark.asyncio
async def test_direct_bus_search():
    """Test direct bus discovery between station pairs with bus connectivity."""
    req = RouteSearchRequest(
        origin="SBC",
        destination="HYB",
        travel_date="2026-10-15",
        max_transfers=2,
        include_buses=True,
    )
    res = await search_routes(req)
    assert res.total_routes_found > 0
    multimodal_routes = [r for r in res.routes if r.is_multimodal]
    assert len(multimodal_routes) > 0
    # First multimodal route has bus legs
    first_multi = multimodal_routes[0]
    assert len(first_multi.bus_legs) > 0
    assert first_multi.bus_legs[0].operator_name is not None
    assert first_multi.bus_legs[0].mode == "BUS"


@pytest.mark.asyncio
async def test_multimodal_intermodal_journey():
    """Test Train -> Bus multimodal journey discovery (e.g. MYS -> HYB via SBC)."""
    req = RouteSearchRequest(
        origin="MYS",
        destination="HYB",
        travel_date="2026-10-15",
        max_transfers=2,
        include_buses=True,
    )
    res = await search_routes(req)
    assert res.total_routes_found > 0
    multi_routes = [r for r in res.routes if r.is_multimodal]
    assert len(multi_routes) > 0
    
    # Check that at least one multimodal route has both train legs and bus legs or intermodal transfers
    found_hybrid = False
    for r in multi_routes:
        if len(r.legs) > 0 and len(r.bus_legs) > 0:
            found_hybrid = True
            # Verify transfer guidance mentions Intermodal
            assert any("Intermodal" in t.interchange_guide for t in r.transfers_info)
            break
    assert found_hybrid, "Expected at least one Train + Bus hybrid route for MYS -> HYB"


@pytest.mark.asyncio
async def test_search_api_multimodal_endpoint():
    """Test live search HTTP endpoint returns valid multimodal response."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "origin": "SBC",
            "destination": "HYB",
            "travel_date": "2026-10-15",
            "max_transfers": 2,
            "include_buses": True,
        }
        resp = await client.post("/api/v1/search", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_routes_found"] > 0
        assert any(r["is_multimodal"] for r in data["routes"])
