"""
Unit tests for Smart Fare Arbitrage Engine.
"""

from app.core.fare_arbitrage import find_upstream_arbitrage


def test_upstream_arbitrage_found():
    # Route: Delhi -> Mathura -> Agra -> Gwalior -> Jhansi -> Bhopal -> Pune
    route = [
        {"station_code": "NDLS", "station_name": "New Delhi"},
        {"station_code": "MTJ", "station_name": "Mathura Junction"},
        {"station_code": "AGC", "station_name": "Agra Cantt"},
        {"station_code": "GWL", "station_name": "Gwalior Junction"},
        {"station_code": "JHS", "station_name": "Jhansi Junction"},
        {"station_code": "BPL", "station_name": "Bhopal Junction"},
        {"station_code": "PUNE", "station_name": "Pune Junction"},
    ]

    # Gwalior (GWL) is sold out (0 seats), but Agra Cantt (AGC) has 8 confirmed seats
    quota = {
        "GWL": 0,
        "AGC": 8,
        "MTJ": 0,
    }
    fares = {
        "GWL": 650,
        "AGC": 650,
    }

    arbitrage = find_upstream_arbitrage(
        route_stops=route,
        origin_code="GWL",
        dest_code="PUNE",
        quota_availability=quota,
        base_fares=fares,
        max_upstream_hops=3,
    )

    assert arbitrage is not None
    assert arbitrage["upstream_code"] == "AGC"
    assert arbitrage["confirmed_seats"] == 8
    assert "Agra Cantt" in arbitrage["tip"]


def test_upstream_arbitrage_not_needed_when_seats_available():
    route = [
        {"station_code": "AGC", "station_name": "Agra Cantt"},
        {"station_code": "GWL", "station_name": "Gwalior Junction"},
        {"station_code": "PUNE", "station_name": "Pune Junction"},
    ]
    # Gwalior already has plenty of seats
    quota = {
        "GWL": 45,
        "AGC": 50,
    }
    fares = {"GWL": 650, "AGC": 650}

    arbitrage = find_upstream_arbitrage(
        route_stops=route,
        origin_code="GWL",
        dest_code="PUNE",
        quota_availability=quota,
        base_fares=fares,
    )
    assert arbitrage is None
