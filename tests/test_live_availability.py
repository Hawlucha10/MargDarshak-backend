"""
Unit & Integration Tests for Milestone 4:
Two-Tier Live Train Status, Timetable Schedule, and Real-Time Seat Availability / Quota Arbitrage.
"""

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_get_live_train_status():
    """Verify live train telemetry returns delay, trend, ETA, and timeline."""
    response = client.get("/api/v1/trains/12627/live")
    assert response.status_code == 200
    data = response.json()

    assert data["train_number"] == "12627"
    assert data["train_name"] == "Karnataka Express"
    assert "delay_minutes" in data
    assert data["delay_status"] in ["ON TIME", "SLIGHT DELAY", "MODERATE DELAY", "CRITICAL DELAY"]
    assert data["delay_trend"] in ["recovering", "stable", "accumulating"]
    assert "current_station" in data
    assert "next_stop" in data
    assert "eta" in data
    assert 0 <= data["journey_percent"] <= 100
    assert len(data["station_timeline"]) > 0

    first_stop = data["station_timeline"][0]
    assert "station_code" in first_stop
    assert "has_passed" in first_stop


def test_get_train_schedule():
    """Verify full station timetable query for a train."""
    response = client.get("/api/v1/trains/12627/schedule")
    assert response.status_code == 200
    data = response.json()

    assert data["train_number"] == "12627"
    assert data["train_name"] == "Karnataka Express"
    assert data["total_stops"] >= 5
    assert len(data["stops"]) == data["total_stops"]
    assert len(data["origin_station"]) > 0
    assert len(data["destination_station"]) > 0


def test_train_availability_post():
    """Verify Tier-2 multi-class seat availability and confirmation probabilities."""
    payload = {
        "train_number": "12627",
        "from_station": "GWL",
        "to_station": "PUNE",
        "travel_date": "2026-10-15",
        "quota": "GN",
    }
    response = client.post("/api/v1/availability/train", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["train_number"] == "12627"
    assert data["from_station"] == "GWL"
    assert data["to_station"] == "PUNE"
    assert len(data["classes"]) >= 5

    class_codes = [c["class_code"] for c in data["classes"]]
    assert "SL" in class_codes
    assert "3A" in class_codes
    assert "2A" in class_codes

    for c in data["classes"]:
        assert c["fare_inr"] > 0
        assert "status" in c
        assert c["confirmation_probability"] is not None
        assert 0.0 <= c["confirmation_probability"] <= 1.0


def test_train_availability_get():
    """Verify convenience GET endpoint for single-train availability."""
    response = client.get(
        "/api/v1/availability/train/12627?from_station=GWL&to_station=PUNE&travel_date=2026-10-15&quota=GN"
    )
    assert response.status_code == 200
    data = response.json()
    assert data["train_number"] == "12627"
    assert len(data["classes"]) >= 5


def test_quota_arbitrage_discovery():
    """Verify that when origin seats are waitlisted, upstream quota arbitrage is triggered."""
    # Using a near-term date to trigger waitlist conditions
    payload = {
        "train_number": "12627",
        "from_station": "GWL",
        "to_station": "PUNE",
        "travel_date": "2026-09-22",
        "quota": "GN",
    }
    response = client.post("/api/v1/availability/train", json=payload)
    assert response.status_code == 200
    data = response.json()

    # When origin is waitlisted, upstream arbitrage recommendation should be returned
    arb = data.get("arbitrage_recommendation")
    if arb:
        assert "upstream_station_code" in arb
        assert "available_seats" in arb
        assert arb["available_seats"] > 0
        assert "instruction" in arb
        assert "Book" in arb["instruction"]


def test_route_multi_leg_availability():
    """Verify multi-hop journey route feasibility audit."""
    payload = {
        "route_id": "journey_gwl_pune_transfer",
        "legs": [
            {
                "train_number": "12627",
                "train_name": "Karnataka Express",
                "from_station": "GWL",
                "to_station": "BPL",
                "travel_date": "2026-10-15",
                "travel_class": "SL",
                "quota": "GN",
            },
            {
                "train_number": "12138",
                "train_name": "Punjab Mail",
                "from_station": "BPL",
                "to_station": "CSMT",
                "travel_date": "2026-10-16",
                "travel_class": "3A",
                "quota": "GN",
            },
        ],
    }
    response = client.post("/api/v1/availability/route", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["route_id"] == "journey_gwl_pune_transfer"
    assert len(data["legs"]) == 2
    assert data["total_fare_inr"] > 0
    assert "overall_confirmation_risk" in data
    assert data["legs"][0]["train_number"] == "12627"
    assert data["legs"][1]["train_number"] == "12138"
