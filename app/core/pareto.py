"""
Multi-Criteria Pareto Optimization for Transit Routes.
Evaluates trade-offs across: Travel Time, Fare, Transfers, Waiting Time, and Reliability.
"""

from typing import List, Dict, Any


def dominates(a: Dict[str, Any], b: Dict[str, Any]) -> bool:
    """
    Returns True if route 'a' Pareto-dominates route 'b'.
    Criteria to MINIMIZE: travel_time, fare, transfers, wait_time
    Criteria to MAXIMIZE: reliability
    """
    # Check if 'a' is no worse than 'b' in all criteria
    no_worse = (
        a["travel_time_min"] <= b["travel_time_min"]
        and a["fare"] <= b["fare"]
        and a["transfers"] <= b["transfers"]
        and a["wait_time_min"] <= b["wait_time_min"]
        and a["reliability"] >= b["reliability"]
    )

    # Check if 'a' is strictly better than 'b' in at least one criterion
    strictly_better = (
        a["travel_time_min"] < b["travel_time_min"]
        or a["fare"] < b["fare"]
        or a["transfers"] < b["transfers"]
        or a["wait_time_min"] < b["wait_time_min"]
        or a["reliability"] > b["reliability"]
    )

    return no_worse and strictly_better


def find_pareto_front(routes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Filters a list of candidate routes to only non-dominated (Pareto-optimal) routes.
    """
    if not routes:
        return []

    pareto_front = []
    for i, candidate in enumerate(routes):
        is_dominated = False
        for j, other in enumerate(routes):
            if i != j and dominates(other, candidate):
                is_dominated = True
                break
        if not is_dominated:
            pareto_front.append(candidate)

    return pareto_front


def assign_pareto_labels(routes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Labels each Pareto-optimal route with human-friendly tags:
    FASTEST, CHEAPEST, FEWEST_TRANSFERS, MOST_RELIABLE, BALANCED.
    """
    if not routes:
        return []

    if len(routes) == 1:
        r_copy = dict(routes[0])
        r_copy["label"] = "BALANCED"
        return [r_copy]

    # Find extreme champions
    fastest = min(routes, key=lambda r: r["travel_time_min"])
    cheapest = min(routes, key=lambda r: r["fare"])
    fewest_transfers = min(routes, key=lambda r: r["transfers"])
    most_reliable = max(routes, key=lambda r: r["reliability"])

    # Comfort champion: min comfort_score or wait_time_min
    most_comfortable = min(
        routes,
        key=lambda r: r.get("comfort_score", r["travel_time_min"] + 3.0 * r.get("wait_time_min", 0))
    )

    # Multimodal champion: fastest multimodal route
    multimodal_candidates = [r for r in routes if r.get("is_multimodal")]
    multimodal_fastest = min(multimodal_candidates, key=lambda r: r["travel_time_min"]) if multimodal_candidates else None

    # Compute min and max for normalization
    min_time = min(r["travel_time_min"] for r in routes)
    max_time = max(r["travel_time_min"] for r in routes)
    time_range = float(max_time - min_time) if max_time > min_time else 1.0

    min_fare = min(r["fare"] for r in routes)
    max_fare = max(r["fare"] for r in routes)
    fare_range = float(max_fare - min_fare) if max_fare > min_fare else 1.0

    # Balanced score (equal weights)
    def balanced_score(r):
        norm_time = (r["travel_time_min"] - min_time) / time_range
        norm_fare = (r["fare"] - min_fare) / fare_range
        norm_transfers = r["transfers"] / 3.0
        norm_reliability = 1.0 - r["reliability"]
        return norm_time + norm_fare + norm_transfers + norm_reliability

    balanced = min(routes, key=balanced_score)

    labeled_routes = []
    assigned_labels = set()

    for r in routes:
        r_copy = dict(r)
        labels = []
        if multimodal_fastest and r is multimodal_fastest and "MULTIMODAL_FASTEST" not in assigned_labels:
            labels.append("MULTIMODAL_FASTEST")
            assigned_labels.add("MULTIMODAL_FASTEST")
        if r is fastest and "FASTEST" not in assigned_labels:
            labels.append("FASTEST")
            assigned_labels.add("FASTEST")
        if r is most_comfortable and r.get("transfers", 0) > 0 and "COMFORT_HOMESTAY" not in assigned_labels:
            labels.append("COMFORT_HOMESTAY")
            assigned_labels.add("COMFORT_HOMESTAY")
        if r is cheapest and "CHEAPEST" not in assigned_labels:
            labels.append("CHEAPEST")
            assigned_labels.add("CHEAPEST")
        if r is fewest_transfers and "FEWEST_TRANSFERS" not in assigned_labels:
            labels.append("FEWEST_TRANSFERS")
            assigned_labels.add("FEWEST_TRANSFERS")
        if r is most_reliable and "MOST_RELIABLE" not in assigned_labels:
            labels.append("MOST_RELIABLE")
            assigned_labels.add("MOST_RELIABLE")
        if r is balanced and "BALANCED" not in assigned_labels:
            labels.append("BALANCED")
            assigned_labels.add("BALANCED")

        r_copy["label"] = labels[0] if labels else ("MULTIMODAL" if r.get("is_multimodal") else "ALTERNATIVE")
        labeled_routes.append(r_copy)

    return labeled_routes
