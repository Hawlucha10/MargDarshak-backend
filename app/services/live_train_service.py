"""
Live Train Telemetry and Schedule Service.
Provides real-time train tracking, delay trend analysis, and station progress.
Backed by PostGIS timetable queries, ML delay prediction, and 60-second Redis caching.
"""

import datetime
import json
import math
import re
import time
from typing import Any, Dict, List, Optional, Tuple

import httpx
from sqlalchemy import text

from app.config import get_settings
from app.db.postgres import get_session_maker
from app.db.redis_client import get_redis
from app.ml.delay_predictor import get_predictor
from app.schemas.train import TrainLiveStatus, TrainScheduleResponse, TrainStop



def _time_str_to_minutes(t_val: Any) -> int:
    """Convert time object or 'HH:MM:SS' string to minutes from midnight."""
    if not t_val or str(t_val).lower() == "none":
        return 0
    s = str(t_val).strip()
    parts = s.split(":")
    if len(parts) >= 2:
        try:
            return int(parts[0]) * 60 + int(parts[1])
        except ValueError:
            return 0
    return 0


def _minutes_to_time_str(minutes: int) -> str:
    """Format minutes from midnight to HH:MM format."""
    normalized = minutes % 1440
    hh = normalized // 60
    mm = normalized % 60
    return f"{hh:02d}:{mm:02d}"


async def fetch_train_stops_db(train_number: str) -> List[Dict[str, Any]]:
    """Fetch ordered train stops from PostgreSQL timetable database."""
    session_maker = get_session_maker()
    clean_num = train_number.strip()

    query = text(
        """
        SELECT 
            t.station_code,
            COALESCE(s.name, t.station_name, t.station_code) AS station_name,
            t.arrival,
            t.departure,
            t.day,
            t.stop_sequence,
            t.train_name,
            s.zone,
            s.lat,
            s.lon
        FROM timetable t
        LEFT JOIN stations s ON t.station_code = s.code
        WHERE t.train_number = :train_number
        ORDER BY t.day ASC, t.stop_sequence ASC, t.id ASC
        """
    )

    try:
        async with session_maker() as session:
            res = await session.execute(query, {"train_number": clean_num})
            rows = res.fetchall()
            if rows:
                return [
                    {
                        "station_code": r.station_code,
                        "station_name": r.station_name,
                        "arrival": str(r.arrival) if r.arrival else None,
                        "departure": str(r.departure) if r.departure else None,
                        "day": r.day or 1,
                        "stop_sequence": r.stop_sequence or (idx + 1),
                        "train_name": r.train_name,
                        "zone": r.zone or "NR",
                        "lat": float(r.lat) if r.lat else None,
                        "lon": float(r.lon) if r.lon else None,
                    }
                    for idx, r in enumerate(rows)
                ]
    except Exception:
        pass
    return []


def _generate_fallback_stops(train_number: str) -> List[Dict[str, Any]]:
    """Synthetic fallback timetable for common corridor trains if DB query is unseeded."""
    known_corridors = {
        "12627": {
            "name": "Karnataka Express",
            "stops": [
                ("NDLS", "New Delhi", "21:15:00", "21:15:00", 1),
                ("AGC", "Agra Cantt", "00:05:00", "00:10:00", 2),
                ("GWL", "Gwalior Junction", "01:25:00", "01:30:00", 2),
                ("JHS", "Jhansi Junction", "02:50:00", "02:58:00", 2),
                ("BINA", "Bina Junction", "05:05:00", "05:10:00", 2),
                ("BPL", "Bhopal Junction", "07:00:00", "07:10:00", 2),
                ("ET", "Itarsi Junction", "08:50:00", "09:00:00", 2),
                ("KNW", "Khandwa Junction", "11:45:00", "11:50:00", 2),
                ("BSL", "Bhusaval Junction", "13:40:00", "13:45:00", 2),
                ("MMR", "Manmad Junction", "16:15:00", "16:20:00", 2),
                ("PUNE", "Pune Junction", "21:45:00", "21:45:00", 2),
            ],
        },
        "12138": {
            "name": "Punjab Mail",
            "stops": [
                ("NDLS", "New Delhi", "05:15:00", "05:15:00", 1),
                ("AGC", "Agra Cantt", "07:55:00", "08:00:00", 1),
                ("GWL", "Gwalior Junction", "09:30:00", "09:35:00", 1),
                ("JHS", "Jhansi Junction", "11:05:00", "11:15:00", 1),
                ("BPL", "Bhopal Junction", "16:25:00", "16:35:00", 1),
                ("ET", "Itarsi Junction", "18:25:00", "18:35:00", 1),
                ("BSL", "Bhusaval Junction", "23:45:00", "23:50:00", 1),
                ("CSMT", "Mumbai CSMT", "07:35:00", "07:35:00", 2),
            ],
        },
    }

    info = known_corridors.get(train_number, {
        "name": f"Express {train_number}",
        "stops": [
            ("NDLS", "New Delhi", "06:00:00", "06:15:00", 1),
            ("CNB", "Kanpur Central", "11:30:00", "11:40:00", 1),
            ("PRYJ", "Prayagraj Junction", "14:10:00", "14:20:00", 1),
            ("DDU", "Pt. DD Upadhyaya", "16:40:00", "16:50:00", 1),
            ("HWH", "Howrah Junction", "23:55:00", "23:55:00", 1),
        ],
    })

    result = []
    for idx, (code, name, arr, dep, day) in enumerate(info["stops"]):
        result.append({
            "station_code": code,
            "station_name": name,
            "arrival": arr,
            "departure": dep,
            "day": day,
            "stop_sequence": idx + 1,
            "train_name": info["name"],
            "zone": "NR",
            "lat": 28.0,
            "lon": 77.0,
        })
    return result


async def _fetch_railkit_live_tracking(
    train_number: str, travel_date: Optional[str] = None
) -> Tuple[bool, Optional[Any], Optional[str]]:
    """
    Calls the RailKit live tracking endpoint:
    GET https://railkit-indian-railway-data.p.rapidapi.com/api/trackTrain/{trainNumber}/{date}
    """
    settings = get_settings()
    if not settings.rapidapi_key:
        return False, None, "RapidAPI key not configured."

    now = datetime.datetime.now()
    if not travel_date:
        formatted_date = now.strftime("%d-%m-%Y")
    else:
        parts = travel_date.split("-")
        if len(parts[0]) == 4:
            formatted_date = f"{parts[2]}-{parts[1]}-{parts[0]}"
        else:
            formatted_date = travel_date

    clean_train = train_number.strip()
    url = f"https://{settings.rapidapi_host}/api/trackTrain/{clean_train}/{formatted_date}"
    headers = {
        "x-rapidapi-key": settings.rapidapi_key,
        "x-rapidapi-host": settings.rapidapi_host,
        "Content-Type": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.get(url, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                if isinstance(data, dict):
                    msg = data.get("message", "")
                    if msg and ("quota" in msg.lower() or "exceeded" in msg.lower()):
                        return False, None, msg
                return True, data, None
            elif resp.status_code == 429:
                return False, None, "RapidAPI quota limit reached."
            else:
                return False, None, f"HTTP {resp.status_code}"
    except Exception as e:
        return False, None, str(e)


def _parse_railkit_live_tracking(train_number: str, data: Dict[str, Any]) -> Optional[TrainLiveStatus]:
    """Parse RailKit live tracking response into TrainLiveStatus."""
    if not isinstance(data, dict):
        return None
    data_dict = data.get("data")
    if not isinstance(data_dict, dict):
        return None

    stations = data_dict.get("stations", [])
    if not stations:
        return None

    train_name = f"Express {train_number}"
    stoppages = [s for s in stations if s.get("type") == "stoppage"]
    all_stations = stoppages if len(stoppages) >= 2 else stations

    # Find current station and next station
    curr_station = all_stations[0]
    next_station = all_stations[1] if len(all_stations) > 1 else all_stations[0]
    curr_idx = 0

    for idx, s in enumerate(all_stations):
        st = s.get("status", "")
        if st in ["departed", "arrived"]:
            curr_station = s
            curr_idx = idx
            if idx + 1 < len(all_stations):
                next_station = all_stations[idx + 1]
            else:
                next_station = s

    # Parse delay minutes
    delay_str = ""
    if next_station.get("arrival", {}).get("delay"):
        delay_str = str(next_station["arrival"]["delay"])
    elif curr_station.get("departure", {}).get("delay"):
        delay_str = str(curr_station["departure"]["delay"])

    delay_minutes = 0
    if "on time" in delay_str.lower():
        delay_minutes = 0
    else:
        nums = re.findall(r'\d+', delay_str)
        if nums:
            delay_minutes = int(nums[0])

    if delay_minutes <= 10:
        delay_status = "ON TIME"
        delay_trend = "stable"
    elif delay_minutes <= 30:
        delay_status = "SLIGHT DELAY"
        delay_trend = "recovering"
    elif delay_minutes <= 60:
        delay_status = "MODERATE DELAY"
        delay_trend = "stable"
    else:
        delay_status = "CRITICAL DELAY"
        delay_trend = "accumulating"

    eta_str = next_station.get("arrival", {}).get("actual") or next_station.get("arrival", {}).get("scheduled") or "On Time"

    total_count = max(1, len(all_stations))
    journey_pct = int(round((curr_idx / max(1, total_count - 1)) * 100))

    try:
        total_dist = int(all_stations[-1].get("distanceKm", 0))
    except Exception:
        total_dist = 500

    try:
        travelled_dist = int(curr_station.get("distanceKm", 0))
    except Exception:
        travelled_dist = int(round(total_dist * (journey_pct / 100.0)))

    timeline: List[TrainStop] = []
    for idx, s in enumerate(all_stations):
        s_code = s.get("stationCode", "")
        s_name = s.get("stationName", "")
        sched_arr = s.get("arrival", {}).get("scheduled")
        sched_dep = s.get("departure", {}).get("scheduled")
        act_arr = s.get("arrival", {}).get("actual")
        act_dep = s.get("departure", {}).get("actual")
        has_passed = s.get("status") in ["departed", "arrived"]
        s_dist = int(s.get("distanceKm", 0)) if str(s.get("distanceKm", "")).isdigit() else idx * 50

        st_del_str = str(s.get("arrival", {}).get("delay") or s.get("departure", {}).get("delay") or "")
        st_delay = 0
        if "on time" not in st_del_str.lower():
            n = re.findall(r'\d+', st_del_str)
            if n:
                st_delay = int(n[0])

        timeline.append(
            TrainStop(
                station_code=s_code,
                station_name=s_name,
                arrival=sched_arr,
                departure=sched_dep,
                day=1,
                stop_sequence=idx + 1,
                distance_km=s_dist,
                delay_minutes=st_delay,
                actual_arrival=act_arr,
                actual_departure=act_dep,
                has_passed=has_passed,
            )
        )

    return TrainLiveStatus(
        train_number=train_number,
        train_name=train_name,
        current_station=curr_station.get("stationCode", ""),
        current_station_name=curr_station.get("stationName", ""),
        delay_minutes=delay_minutes,
        delay_status=delay_status,
        delay_trend=delay_trend,
        next_stop=next_station.get("stationCode", ""),
        next_stop_name=next_station.get("stationName", ""),
        eta=eta_str,
        journey_percent=journey_pct,
        distance_travelled_km=travelled_dist,
        total_distance_km=total_dist,
        station_timeline=timeline,
        updated_at="Live GPS / PRS",
        source="railkit_live_tracking_api",
        cached=False,
    )


async def get_live_train_status(train_number: str, travel_date: Optional[str] = None) -> TrainLiveStatus:
    """Retrieve live running status for a train via the active RailwayGateway."""
    from app.services.gateway import get_railway_gateway
    return await get_railway_gateway().get_live_train_status(train_number, travel_date)

async def get_train_schedule(train_number: str) -> TrainScheduleResponse:
    """Retrieve full station timetable for a train via active RailwayGateway."""
    from app.services.gateway import get_railway_gateway
    return await get_railway_gateway().get_train_schedule(train_number)

