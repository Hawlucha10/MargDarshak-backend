"""
Bus Service Layer for MargDarshak
Provides bus route discovery, terminal lookup, and fare estimation.
"""

from typing import Any, Dict, List, Optional
from datetime import time as dt_time
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.postgres import get_session_maker


async def get_connecting_buses(
    from_station_code: str,
    to_station_code: str,
    after_time: Optional[str] = None,
    limit: int = 5,
) -> List[Dict[str, Any]]:
    """
    Find bus routes that bridge a train layover between two railway stations.
    Looks up bus terminals near both stations and returns connecting buses.
    """
    session_maker = get_session_maker()
    async with session_maker() as session:
        query = text("""
            SELECT
                br.route_id, br.route_code, br.bus_type,
                br.departure, br.arrival, br.duration_minutes,
                br.distance_km, br.fare, br.is_ac, br.is_sleeper,
                br.has_charging, br.has_wifi, br.rating,
                bo.name as operator_name, bo.short_code as operator_code,
                bo.operator_type,
                ft.name as from_terminal, ft.transfer_walk_minutes as from_walk,
                tt.name as to_terminal, tt.transfer_walk_minutes as to_walk
            FROM bus_routes br
            JOIN bus_operators bo ON br.operator_id = bo.operator_id
            JOIN bus_terminals ft ON br.from_terminal_id = ft.terminal_id
            JOIN bus_terminals tt ON br.to_terminal_id = tt.terminal_id
            WHERE ft.nearest_station_code = :from_stn
              AND tt.nearest_station_code = :to_stn
              AND (:after_time IS NULL OR br.departure >= :after_time::time)
            ORDER BY br.departure ASC
            LIMIT :lim
        """)

        result = await session.execute(query, {
            "from_stn": from_station_code.upper(),
            "to_stn": to_station_code.upper(),
            "after_time": after_time,
            "lim": limit,
        })

        buses = []
        for row in result.fetchall():
            dep_str = row.departure.strftime("%H:%M") if row.departure else None
            arr_str = row.arrival.strftime("%H:%M") if row.arrival else None
            buses.append({
                "route_id": row.route_id,
                "route_code": row.route_code,
                "operator_name": row.operator_name,
                "operator_code": row.operator_code,
                "operator_type": row.operator_type,
                "bus_type": row.bus_type,
                "departure": dep_str,
                "arrival": arr_str,
                "duration_minutes": row.duration_minutes,
                "distance_km": row.distance_km,
                "fare": row.fare,
                "is_ac": row.is_ac,
                "is_sleeper": row.is_sleeper,
                "has_charging": row.has_charging,
                "has_wifi": row.has_wifi,
                "rating": float(row.rating) if row.rating else None,
                "from_terminal": row.from_terminal,
                "from_walk_minutes": row.from_walk,
                "to_terminal": row.to_terminal,
                "to_walk_minutes": row.to_walk,
                "total_transfer_time": (row.from_walk or 15) + row.duration_minutes + (row.to_walk or 15),
            })
        return buses


async def get_bus_terminals_near_station(
    station_code: str,
    radius_km: float = 5.0,
) -> List[Dict[str, Any]]:
    """Find bus terminals near a railway station."""
    session_maker = get_session_maker()
    async with session_maker() as session:
        query = text("""
            SELECT
                bt.terminal_id, bt.name, bt.city, bt.state,
                bt.lat, bt.lon, bt.nearest_station_code,
                bt.transfer_walk_minutes, bt.terminal_type, bt.amenities,
                ST_Distance(
                    bt.geom::geography,
                    s.geom::geography
                ) / 1000.0 as distance_km
            FROM bus_terminals bt
            JOIN stations s ON s.code = :stn_code
            WHERE ST_DWithin(
                bt.geom::geography,
                s.geom::geography,
                :radius_m
            )
            ORDER BY distance_km ASC
        """)

        result = await session.execute(query, {
            "stn_code": station_code.upper(),
            "radius_m": radius_km * 1000,
        })

        return [
            {
                "terminal_id": row.terminal_id,
                "name": row.name,
                "city": row.city,
                "state": row.state,
                "lat": float(row.lat),
                "lon": float(row.lon),
                "nearest_station_code": row.nearest_station_code,
                "walk_minutes": row.transfer_walk_minutes,
                "terminal_type": row.terminal_type,
                "amenities": row.amenities or [],
                "distance_km": round(float(row.distance_km), 2) if row.distance_km else None,
            }
            for row in result.fetchall()
        ]


def estimate_bus_fare(distance_km: float, bus_type: str = "ORDINARY") -> int:
    """Estimate bus fare based on distance and bus type."""
    FARE_RATES = {
        "ORDINARY": 1.0,
        "EXPRESS": 1.3,
        "DELUXE": 1.6,
        "AC_SEATER": 2.0,
        "SUPER_DELUXE": 2.2,
        "AC_SLEEPER": 2.8,
        "VOLVO_MULTI_AXLE": 2.5,
        "ELECTRIC_AC": 2.3,
    }
    base_rate = 1.2  # INR per km
    multiplier = FARE_RATES.get(bus_type, 1.0)
    return max(50, int(distance_km * base_rate * multiplier))
