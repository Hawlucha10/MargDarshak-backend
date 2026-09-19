"""
Smart Fare Arbitrage Engine
Scans upstream stations along the same train route to discover available quota
and distance-slab fare savings when seats are waitlisted at the origin station.
"""

from typing import List, Dict, Any, Optional


def find_upstream_arbitrage(
    route_stops: List[Dict[str, Any]],
    origin_code: str,
    dest_code: str,
    quota_availability: Dict[str, int],
    base_fares: Dict[str, int],
    max_upstream_hops: int = 5,
) -> Optional[Dict[str, Any]]:
    """
    Checks up to `max_upstream_hops` stations preceding `origin_code`.
    If seats from origin are 0 (or Waitlist), checks if an upstream station
    has confirmed seats and calculates fare differential.
    """
    origin_code = origin_code.upper()
    dest_code = dest_code.upper()

    # Find index of origin and destination in route sequence
    stop_codes = [s["station_code"].upper() for s in route_stops]
    if origin_code not in stop_codes or dest_code not in stop_codes:
        return None

    idx_origin = stop_codes.index(origin_code)
    idx_dest = stop_codes.index(dest_code)

    if idx_origin >= idx_dest:
        return None  # Invalid direction

    origin_seats = quota_availability.get(origin_code, 0)
    origin_fare = base_fares.get(origin_code, 0)

    # If seats are already confirmed and abundant, arbitrage is optional/low priority
    # But if waitlisted (<=0) or low availability, check upstream
    upstream_start = max(0, idx_origin - max_upstream_hops)
    candidates = []

    for i in range(upstream_start, idx_origin):
        upstream_station = route_stops[i]
        u_code = upstream_station["station_code"].upper()
        u_name = upstream_station.get("station_name", u_code)
        u_seats = quota_availability.get(u_code, 0)
        u_fare = base_fares.get(u_code, origin_fare)

        # Arbitrage is valid if upstream has confirmed seats
        if u_seats > 0 and (origin_seats <= 0 or u_seats > origin_seats + 5):
            savings = origin_fare - u_fare
            candidates.append({
                "upstream_code": u_code,
                "upstream_name": u_name,
                "confirmed_seats": u_seats,
                "upstream_fare": u_fare,
                "origin_fare": origin_fare,
                "savings": max(0, savings),
                "tip": (
                    f"💡 Confirmed seats ({u_seats} available) from {u_name} ({u_code})! "
                    f"Book from {u_code} to {dest_code} and set your boarding station as {origin_code}."
                ),
            })

    if not candidates:
        return None

    # Pick the candidate with the highest confirmed seats or highest savings
    best = max(candidates, key=lambda c: (c["confirmed_seats"], c["savings"]))
    return best
