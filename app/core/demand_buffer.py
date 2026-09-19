"""
Demand-Adaptive Buffer Time Engine
Dynamically adjusts connection transfer buffer times during national festival and peak holiday windows.
"""

from datetime import datetime, date
from typing import Dict, Any, Tuple


# Notable Indian high-congestion transit windows (ranges cover pre/post festival travel surge)
FESTIVAL_SURGE_WINDOWS = [
    # Diwali & Chhath Puja rush (Northern & Eastern corridors experience 2x-3x passenger surge)
    {"name": "Diwali & Chhath Puja Rush", "start": (10, 20), "end": (11, 15), "multiplier": 1.75, "min_extra_buffer": 35},
    # Holi holiday travel surge
    {"name": "Holi Festival Rush", "start": (3, 10), "end": (3, 28), "multiplier": 1.40, "min_extra_buffer": 20},
    # Summer vacation heavy transit peak
    {"name": "Summer Holiday Peak", "start": (5, 1), "end": (6, 20), "multiplier": 1.30, "min_extra_buffer": 15},
    # Durga Puja / Dussehra travel
    {"name": "Navratri & Durga Puja Surge", "start": (9, 25), "end": (10, 15), "multiplier": 1.45, "min_extra_buffer": 25},
    # Year-end winter peak & fog overlap
    {"name": "Winter Holiday Peak", "start": (12, 22), "end": (1, 5), "multiplier": 1.60, "min_extra_buffer": 30},
]


def get_demand_adaptive_buffer(
    travel_date_str: str,
    base_buffer_min: int = 30,
) -> Dict[str, Any]:
    """
    Computes demand-adaptive buffer time for a given travel date.
    Returns effective buffer minutes, surge multiplier, and reason.
    """
    try:
        if isinstance(travel_date_str, (datetime, date)):
            d = travel_date_str
        else:
            d = datetime.strptime(travel_date_str.strip(), "%Y-%m-%d").date()
    except Exception:
        d = date.today()

    month, day = d.month, d.day

    active_surge = None
    for surge in FESTIVAL_SURGE_WINDOWS:
        start_m, start_d = surge["start"]
        end_m, end_d = surge["end"]

        # Handle windows within same year or crossing new year
        if start_m <= end_m:
            in_window = (start_m < month < end_m) or (month == start_m and day >= start_d) or (month == end_m and day <= end_d)
        else:
            in_window = (month > start_m or (month == start_m and day >= start_d)) or (month < end_m or (month == end_m and day <= end_d))

        if in_window:
            active_surge = surge
            break

    if active_surge:
        scaled_buffer = int(base_buffer_min * active_surge["multiplier"])
        effective_buffer = max(scaled_buffer, base_buffer_min + active_surge["min_extra_buffer"])
        return {
            "is_peak_demand": True,
            "festival_name": active_surge["name"],
            "base_buffer_min": base_buffer_min,
            "effective_buffer_min": effective_buffer,
            "added_buffer_min": effective_buffer - base_buffer_min,
            "multiplier": active_surge["multiplier"],
            "explanation": (
                f"📊 {active_surge['name']}: Connection buffer dynamically increased from "
                f"{base_buffer_min}m to {effective_buffer}m (+{effective_buffer - base_buffer_min}m) "
                f"to protect against seasonal platform crowding and rake delays."
            ),
        }

    # Off-peak regular buffer
    return {
        "is_peak_demand": False,
        "festival_name": None,
        "base_buffer_min": base_buffer_min,
        "effective_buffer_min": base_buffer_min,
        "added_buffer_min": 0,
        "multiplier": 1.0,
        "explanation": "Standard seasonal buffer applied.",
    }
