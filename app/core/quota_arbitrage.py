"""
Cross-Zone Quota Arbitrage Engine
Scans multi-tier Indian Railway booking quotas (General GN, Remote Location RLGN,
Pooled PQ, Tatkal TQ) across neighboring stations to unlock confirmed berths on sold-out trains.
"""

from typing import List, Dict, Any, Optional


def find_cross_quota_arbitrage(
    route_stations: List[Dict[str, Any]],
    user_origin_code: str,
    user_dest_code: str,
    multi_quota_availability: Dict[str, Dict[str, Any]],
    base_fares: Dict[str, int],
) -> Optional[Dict[str, Any]]:
    """
    Scans for opportunities where General Quota (GN) is full/waitlisted from user_origin,
    but a Remote Location Quota (RLGN/RLWL) or Origin Quota from a nearby upstream station
    has confirmed berths at favorable distance-tier pricing.
    """
    origin = user_origin_code.upper()
    dest = user_dest_code.upper()

    station_codes = [s["station_code"].upper() for s in route_stations]
    if origin not in station_codes or dest not in station_codes:
        return None

    orig_idx = station_codes.index(origin)
    dest_idx = station_codes.index(dest)
    if orig_idx >= dest_idx:
        return None

    # Origin station quota status
    origin_quotas = multi_quota_availability.get(origin, {})
    origin_gn_status = origin_quotas.get("GN", {}).get("status", "AVAILABLE")
    origin_gn_seats = origin_quotas.get("GN", {}).get("seats", 0)

    # If already confirmed with plenty of seats, no quota arbitrage needed
    if origin_gn_status == "AVAILABLE" and origin_gn_seats > 10:
        return None

    # Scan upstream stations (up to 5 stops before user origin)
    upstream_window = max(0, orig_idx - 5)
    candidates = []

    for i in range(upstream_window, orig_idx):
        st = route_stations[i]
        st_code = st["station_code"].upper()
        st_name = st.get("station_name", st_code)

        st_quotas = multi_quota_availability.get(st_code, {})
        for quota_type, quota_info in st_quotas.items():
            q_status = quota_info.get("status", "REGRET")
            q_seats = quota_info.get("seats", 0)

            # Look for confirmed seats under GN or Remote Location RLGN
            if q_status == "AVAILABLE" and q_seats > 0:
                upstream_fare = base_fares.get(st_code, base_fares.get(origin, 500))
                origin_fare = base_fares.get(origin, 500)
                savings = origin_fare - upstream_fare

                candidates.append({
                    "station_code": st_code,
                    "station_name": st_name,
                    "quota_type": quota_type,
                    "quota_name": "Remote Location Quota (RLGN)" if quota_type == "RLGN" else f"{quota_type} Quota",
                    "available_seats": q_seats,
                    "ticket_fare": upstream_fare,
                    "origin_fare": origin_fare,
                    "fare_difference": savings,
                    "instruction": (
                        f"🔄 Quota Arbitrage Found: While {origin} has {origin_gn_status} under General Quota, "
                        f"{st_name} ({st_code}) has {q_seats} Confirmed seats under {quota_type}! "
                        f"Book ticket {st_code} ➔ {dest} and select boarding point as {origin}."
                    ),
                })

    if not candidates:
        return None

    # Sort by confirmed seats available and lowest price
    best_candidate = max(candidates, key=lambda c: (c["available_seats"], c["fare_difference"]))
    return best_candidate
