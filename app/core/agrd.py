"""
Adaptive Geo-Radial Route Discovery (AGRD)
Discovers all intermediate junction stations in a geographic search zone between Origin and Destination.
"""

import math
from typing import List, Dict, Any, Optional
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates the great-circle distance between two points in kilometers."""
    R = 6371.0  # Earth's radius in kilometers

    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c


def point_in_ellipse(
    lat: float,
    lon: float,
    orig_lat: float,
    orig_lon: float,
    dest_lat: float,
    dest_lon: float,
    focal_slack: float = 1.3,
) -> bool:
    """
    Checks if a station (lat, lon) is within the search ellipse defined by foci (orig, dest).
    Property of ellipse: dist(P, Focus1) + dist(P, Focus2) <= 2 * a
    where 2 * a = direct_distance * focal_slack.
    """
    d_direct = haversine_distance_km(orig_lat, orig_lon, dest_lat, dest_lon)
    max_combined_dist = d_direct * focal_slack

    d1 = haversine_distance_km(lat, lon, orig_lat, orig_lon)
    d2 = haversine_distance_km(lat, lon, dest_lat, dest_lon)

    return (d1 + d2) <= max_combined_dist


async def discover_stations_postgis(
    session: AsyncSession,
    origin_code: str,
    dest_code: str,
    focal_slack: float = 1.3,
) -> List[Dict[str, Any]]:
    """
    Executes an optimized PostGIS spatial query to discover candidate stations
    inside the focal search ellipse between origin and destination.
    """
    # 1. Fetch coordinates of origin and destination
    query_coords = text(
        """
        SELECT code, name, lat, lon 
        FROM stations 
        WHERE code IN (:orig, :dest)
        """
    )
    result = await session.execute(query_coords, {"orig": origin_code.upper(), "dest": dest_code.upper()})
    coords = {row.code: {"name": row.name, "lat": float(row.lat), "lon": float(row.lon)} for row in result.fetchall()}

    if origin_code.upper() not in coords or dest_code.upper() not in coords:
        raise ValueError(f"Station codes not found: {origin_code} or {dest_code}")

    orig = coords[origin_code.upper()]
    dest = coords[dest_code.upper()]

    direct_dist = haversine_distance_km(orig["lat"], orig["lon"], dest["lat"], dest["lon"])
    max_dist_meters = (direct_dist * focal_slack) * 1000.0

    # 2. PostGIS spatial query: sum of distances from origin and destination <= max_dist
    query_ellipse = text(
        """
        SELECT code, name, zone, state, lat, lon
        FROM stations
        WHERE (
            ST_Distance(geom::geography, ST_SetSRID(ST_MakePoint(:orig_lon, :orig_lat), 4326)::geography) +
            ST_Distance(geom::geography, ST_SetSRID(ST_MakePoint(:dest_lon, :dest_lat), 4326)::geography)
        ) <= :max_dist
        ORDER BY name ASC
        """
    )

    ellipse_res = await session.execute(
        query_ellipse,
        {
            "orig_lat": orig["lat"],
            "orig_lon": orig["lon"],
            "dest_lat": dest["lat"],
            "dest_lon": dest["lon"],
            "max_dist": max_dist_meters,
        },
    )

    discovered = [
        {
            "code": row.code,
            "name": row.name,
            "zone": row.zone,
            "state": row.state,
            "lat": float(row.lat),
            "lon": float(row.lon),
        }
        for row in ellipse_res.fetchall()
    ]
    return discovered
