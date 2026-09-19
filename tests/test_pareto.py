"""
Unit tests for Pareto Optimization logic.
"""

from app.core.pareto import dominates, find_pareto_front, assign_pareto_labels


def test_pareto_dominance():
    # Route A: Faster and cheaper than Route B with same transfers
    route_a = {"travel_time_min": 600, "fare": 400, "transfers": 1, "wait_time_min": 45, "reliability": 0.90}
    route_b = {"travel_time_min": 750, "fare": 550, "transfers": 1, "wait_time_min": 60, "reliability": 0.85}

    assert dominates(route_a, route_b) is True
    assert dominates(route_b, route_a) is False


def test_pareto_trade_off():
    # Route A is faster, but Route B is cheaper -> neither dominates
    route_a = {"id": "A", "travel_time_min": 500, "fare": 800, "transfers": 1, "wait_time_min": 30, "reliability": 0.90}
    route_b = {"id": "B", "travel_time_min": 800, "fare": 350, "transfers": 1, "wait_time_min": 45, "reliability": 0.90}

    assert dominates(route_a, route_b) is False
    assert dominates(route_b, route_a) is False

    front = find_pareto_front([route_a, route_b])
    assert len(front) == 2


def test_assign_labels():
    routes = [
        {"id": "A", "travel_time_min": 400, "fare": 900, "transfers": 1, "wait_time_min": 30, "reliability": 0.85},
        {"id": "B", "travel_time_min": 900, "fare": 300, "transfers": 2, "wait_time_min": 60, "reliability": 0.80},
        {"id": "C", "travel_time_min": 600, "fare": 600, "transfers": 0, "wait_time_min": 0, "reliability": 0.95},
    ]
    labeled = assign_pareto_labels(routes)
    labels = {r["id"]: r["label"] for r in labeled}

    assert labels["A"] == "FASTEST"
    assert labels["B"] == "CHEAPEST"
    assert labels["C"] in ("FEWEST_TRANSFERS", "MOST_RELIABLE")
