"""
Unit and integration tests for all 6 Patent-Level Features.
"""

from app.core.reliability import compute_joint_route_reliability, calculate_connection_probability
from app.services.weather_service import WeatherAwareRouter
from app.core.demand_buffer import get_demand_adaptive_buffer
from app.core.quota_arbitrage import find_cross_quota_arbitrage
from app.core.accessibility import evaluate_station_accessibility, audit_route_accessibility
from app.services.nlp_search import parse_natural_language_query


def test_probabilistic_joint_reliability():
    legs = [
        {"to_station": "BPL", "predicted_delay_min": 25},
        {"to_station": "PUNE", "predicted_delay_min": 10},
    ]
    # Tight buffer (30m with 15m walk = 15m slack vs 25m delay) -> moderate/low prob
    rel_tight = compute_joint_route_reliability(legs, transfer_buffers_min=[30])
    # Generous buffer (75m with 15m walk = 60m slack vs 25m delay) -> very high prob
    rel_safe = compute_joint_route_reliability(legs, transfer_buffers_min=[75])

    assert rel_safe["joint_reliability_score"] > rel_tight["joint_reliability_score"]
    assert "%" in rel_safe["joint_reliability_percent"]


def test_weather_aware_routing_hazard_detection():
    router = WeatherAwareRouter()
    # Route through cyclone impacted stations (VSKP)
    audit = router.inspect_route_weather(station_codes=["HWH", "VSKP", "MAS"])
    assert audit["has_weather_impact"] is True
    assert audit["weather_status"] == "CRITICAL"
    assert audit["should_reroute"] is True
    assert audit["weather_delay_penalty_min"] >= 120


def test_demand_adaptive_buffer_diwali():
    # November 5th (Diwali peak season)
    buf_diwali = get_demand_adaptive_buffer("2026-11-05", base_buffer_min=30)
    assert buf_diwali["is_peak_demand"] is True
    assert "Diwali" in buf_diwali["festival_name"]
    assert buf_diwali["effective_buffer_min"] >= 50

    # April 10th (Regular non-peak)
    buf_regular = get_demand_adaptive_buffer("2026-04-10", base_buffer_min=30)
    assert buf_regular["is_peak_demand"] is False
    assert buf_regular["effective_buffer_min"] == 30


def test_cross_zone_quota_arbitrage():
    route = [
        {"station_code": "AGC", "station_name": "Agra Cantt"},
        {"station_code": "GWL", "station_name": "Gwalior Junction"},
        {"station_code": "PUNE", "station_name": "Pune Junction"},
    ]
    quotas = {
        "GWL": {"GN": {"status": "WL_45", "seats": 0}},
        "AGC": {"RLGN": {"status": "AVAILABLE", "seats": 14}},
    }
    fares = {"GWL": 700, "AGC": 700}

    arb = find_cross_quota_arbitrage(route, "GWL", "PUNE", quotas, fares)
    assert arb is not None
    assert arb["station_code"] == "AGC"
    assert arb["quota_type"] == "RLGN"
    assert arb["available_seats"] == 14


def test_accessibility_first_routing():
    # Bhopal has lifts, ramps, and battery cart
    bpl = evaluate_station_accessibility("BPL")
    assert bpl["is_step_free"] is True
    assert bpl["has_lifts"] is True

    # Audit route requiring step-free access
    audit = audit_route_accessibility(["GWL", "BPL", "PUNE"], require_step_free=True)
    assert audit["is_accessible_route"] is True
    assert "♿" in audit["accessibility_badge"]


def test_nlp_search_english_and_hindi():
    # English natural language query
    q_en = "Cheapest train from Gwalior to Pune next weekend"
    parsed_en = parse_natural_language_query(q_en)
    req_en = parsed_en["parsed_request"]
    assert req_en.origin == "GWL"
    assert req_en.destination == "PUNE"
    assert req_en.priority == "cheapest"

    # Hindi natural language query
    q_hi = "पुणे से दिल्ली सबसे सस्ता रास्ता"
    parsed_hi = parse_natural_language_query(q_hi)
    req_hi = parsed_hi["parsed_request"]
    assert req_hi.origin == "PUNE"
    assert req_hi.destination == "NDLS"
    assert req_hi.priority == "cheapest"
