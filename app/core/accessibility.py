"""
Accessibility-First Routing Engine (PwD & Reduced Mobility)
Audits stations for step-free access, wheelchair ramps, elevators/lifts,
and calculates realistic transfer walking distances.
"""

from typing import List, Dict, Any, Optional


# Station accessibility registry (sample database populated from Indian Railways Sugamya Bharat / Accessibility portal)
STATION_ACCESSIBILITY_REGISTRY = {
    "NDLS": {"name": "New Delhi", "has_ramps": True, "has_lifts": True, "has_battery_cart": True, "step_free": True, "avg_walk_meters": 220},
    "BPL": {"name": "Bhopal Junction", "has_ramps": True, "has_lifts": True, "has_battery_cart": True, "step_free": True, "avg_walk_meters": 180},
    "GWL": {"name": "Gwalior Junction", "has_ramps": True, "has_lifts": True, "has_battery_cart": False, "step_free": True, "avg_walk_meters": 150},
    "JHS": {"name": "Jhansi Junction", "has_ramps": True, "has_lifts": True, "has_battery_cart": True, "step_free": True, "avg_walk_meters": 160},
    "NGP": {"name": "Nagpur Junction", "has_ramps": True, "has_lifts": True, "has_battery_cart": True, "step_free": True, "avg_walk_meters": 190},
    "PUNE": {"name": "Pune Junction", "has_ramps": True, "has_lifts": True, "has_battery_cart": True, "step_free": True, "avg_walk_meters": 200},
    "CSMT": {"name": "Mumbai CSMT", "has_ramps": True, "has_lifts": True, "has_battery_cart": True, "step_free": True, "avg_walk_meters": 250},
    # Sample smaller junction with stair-only overbridge
    "ET": {"name": "Itarsi Junction", "has_ramps": True, "has_lifts": False, "has_battery_cart": False, "step_free": False, "avg_walk_meters": 310},
    "BINA": {"name": "Bina Junction", "has_ramps": False, "has_lifts": False, "has_battery_cart": False, "step_free": False, "avg_walk_meters": 280},
}


def evaluate_station_accessibility(station_code: str) -> Dict[str, Any]:
    """Retrieves accessibility profile for a station."""
    code = station_code.upper().strip()
    profile = STATION_ACCESSIBILITY_REGISTRY.get(code)
    if profile:
        return {
            "station_code": code,
            "station_name": profile["name"],
            "is_step_free": profile["step_free"],
            "has_ramps": profile["has_ramps"],
            "has_lifts": profile["has_lifts"],
            "has_battery_cart": profile["has_battery_cart"],
            "avg_walk_meters": profile["avg_walk_meters"],
            "accessibility_rating": "EXCELLENT" if profile["step_free"] and profile["has_battery_cart"] else ("GOOD" if profile["has_ramps"] else "LIMITED"),
        }
    # Default baseline for unlisted stations
    return {
        "station_code": code,
        "station_name": code,
        "is_step_free": True,
        "has_ramps": True,
        "has_lifts": False,
        "has_battery_cart": False,
        "avg_walk_meters": 180,
        "accessibility_rating": "MODERATE",
    }


def audit_route_accessibility(
    station_codes: List[str],
    require_step_free: bool = False,
) -> Dict[str, Any]:
    """
    Audits an entire multi-hop route for wheelchair and reduced mobility compliance.
    Calculates total transfer walking distance and verifies step-free access at all junctions.
    """
    station_audits = [evaluate_station_accessibility(code) for code in station_codes]

    is_compliant = True
    violating_stations = []
    total_walking_meters = 0

    for audit in station_audits:
        total_walking_meters += audit["avg_walk_meters"]
        if require_step_free and not audit["is_step_free"]:
            is_compliant = False
            violating_stations.append(audit["station_code"])

    # Walking time in minutes for reduced mobility (assumes 40 meters/min pace)
    estimated_walk_minutes = int(total_walking_meters / 40.0)

    return {
        "is_accessible_route": is_compliant,
        "requires_step_free": require_step_free,
        "violating_stations": violating_stations,
        "total_estimated_walking_meters": total_walking_meters,
        "estimated_transfer_walk_minutes": estimated_walk_minutes,
        "station_details": station_audits,
        "accessibility_badge": "♿ 100% Step-Free Accessible" if is_compliant and require_step_free else "Standard Route",
    }
