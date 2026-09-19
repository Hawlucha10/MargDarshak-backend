"""
Dynamic Weather-Aware Routing Service (IMD Integration)
Monitors India Meteorological Department (IMD) alerts (cyclones, dense fog, flood warnings)
and dynamically flags or penalizes disrupted railway corridors.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime


# Standardized hazard zones mapped to Indian Railways administrative zones & coastal regions
DEFAULT_WEATHER_HAZARDS = [
    {
        "hazard_id": "CYCLONE_BOB_01",
        "type": "CYCLONE",
        "severity": "CRITICAL",
        "name": "Bay of Bengal Deep Depression Warning",
        "affected_zones": ["ECOR", "SER", "SR"],
        "affected_stations": ["VSKP", "BBS", "PURI", "BAM", "PSA", "RJY", "BZA"],
        "recommended_action": "AVOID_COASTAL_LINE",
        "delay_penalty_minutes": 180,
        "active_until": "2026-11-30",
        "description": "Severe cyclonic circulation near Andhra/Odisha coast. Track speed restricted to 45 km/h.",
    },
    {
        "hazard_id": "FOG_RED_02",
        "type": "DENSE_FOG",
        "severity": "HIGH",
        "name": "North India Dense Fog Red Alert",
        "affected_zones": ["NR", "NCR", "NER"],
        "affected_stations": ["NDLS", "DLI", "CNB", "ALJN", "AGC", "GWL", "PRYJ", "BSB"],
        "recommended_action": "INFLATE_CHANGE_BUFFERS",
        "delay_penalty_minutes": 75,
        "active_until": "2026-02-28",
        "description": "Zero visibility fog conditions on Delhi-Kanpur-Prayagraj Grand Trunk route.",
    },
    {
        "hazard_id": "GHATS_LANDSLIDE_03",
        "type": "MONSOON_FLOOD",
        "severity": "HIGH",
        "name": "Western Ghats Flash Flood Warning",
        "affected_zones": ["KR", "CR"],
        "affected_stations": ["RN", "MAO", "KAWR", "UD", "MAJN"],
        "recommended_action": "INCREASE_CONNECTION_SLACK",
        "delay_penalty_minutes": 90,
        "active_until": "2026-09-30",
        "description": "Heavy rainfall warning on Konkan Railway route with boulder net checks.",
    },
]


class WeatherAwareRouter:
    """
    Evaluates railway routes against active IMD meteorological advisories.
    """

    def __init__(self, active_hazards: Optional[List[Dict[str, Any]]] = None):
        self.hazards = active_hazards or DEFAULT_WEATHER_HAZARDS

    def inspect_route_weather(
        self,
        station_codes: List[str],
        zones: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Inspects if any station or railway zone on the journey falls within an active weather hazard.
        Returns weather risk rating, active advisories, and reroute recommendation.
        """
        station_set = set(code.upper() for code in station_codes)
        zone_set = set(z.upper() for z in (zones or []))

        active_advisories = []
        total_delay_penalty = 0
        max_severity = "CLEAR"

        for hazard in self.hazards:
            hazard_stations = set(hazard.get("affected_stations", []))
            hazard_zones = set(hazard.get("affected_zones", []))

            station_intersect = station_set.intersection(hazard_stations)
            zone_intersect = zone_set.intersection(hazard_zones)

            if station_intersect or zone_intersect:
                impacted = list(station_intersect) or list(zone_intersect)
                active_advisories.append({
                    "hazard_name": hazard["name"],
                    "type": hazard["type"],
                    "severity": hazard["severity"],
                    "impacted_entities": impacted,
                    "action": hazard["recommended_action"],
                    "description": hazard["description"],
                    "delay_penalty_min": hazard["delay_penalty_minutes"],
                })

                total_delay_penalty = max(total_delay_penalty, hazard["delay_penalty_minutes"])

                if hazard["severity"] == "CRITICAL":
                    max_severity = "CRITICAL"
                elif hazard["severity"] == "HIGH" and max_severity != "CRITICAL":
                    max_severity = "HIGH"
                elif max_severity == "CLEAR":
                    max_severity = "MODERATE"

        should_reroute = (max_severity == "CRITICAL")
        reroute_advice = None

        if should_reroute:
            reroute_advice = (
                "⚠️ IMD Alert: Critical weather warning on primary corridor. "
                "Automatically prioritizing inland bypass route via central corridor."
            )

        return {
            "weather_status": max_severity,
            "has_weather_impact": len(active_advisories) > 0,
            "should_reroute": should_reroute,
            "reroute_advice": reroute_advice,
            "weather_delay_penalty_min": total_delay_penalty,
            "active_advisories": active_advisories,
        }
