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

    # 1. Redis Cache Check (120-second TTL to conserve API quota)
    try:
        redis = get_redis()
        cached_data = await redis.get(cache_key)
        if cached_data:
            data = json.loads(cached_data)
            data["cached"] = True
            return TrainLiveStatus(**data)
    except Exception:
        pass

    # 2. Query RailKit RapidAPI live tracking endpoint
    api_success, api_data, error_msg = await _fetch_railkit_live_tracking(clean_num, travel_date)
    if api_success and api_data:
        live_status = _parse_railkit_live_tracking(clean_num, api_data)
        if live_status:
            try:
                redis = get_redis()
                await redis.set(cache_key, live_status.model_dump_json(), ex=120)
            except Exception:
                pass
            return live_status

    # 3. Fallback to Local Timetable + ML Delay Prediction if API unavailable
    stops_data = await fetch_train_stops_db(clean_num)
    if not stops_data:
        stops_data = _generate_fallback_stops(clean_num)


    train_name = stops_data[0].get("train_name", f"Express {clean_num}")
    total_stops = len(stops_data)

    # 3. Predict ML Delay for Today
    now = datetime.datetime.now()
    current_month = now.month
    primary_zone = stops_data[0].get("zone", "NR")

    predictor = get_predictor()
    pred_res = predictor.predict_delay(
        train_number=clean_num,
        month=current_month,
        zone=primary_zone,
        distance_km=max(300, total_stops * 95),
    )
    delay_minutes = int(round(pred_res.get("predicted_delay_minutes", 15)))

    # Determine delay category and telemetry trend
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

    # 4. Compute Simulated Train Position along the Route
    # Determine current station index (proportional to time of day or mid-route progression)
    time_of_day_ratio = ((now.hour * 60 + now.minute) % 1440) / 1440.0
    curr_idx = min(total_stops - 2, max(0, int(round(time_of_day_ratio * (total_stops - 1)))))
    next_idx = min(total_stops - 1, curr_idx + 1)

    curr_stop = stops_data[curr_idx]
    next_stop = stops_data[next_idx]

    # Calculate ETA to next station
    next_sched_arr_min = _time_str_to_minutes(next_stop.get("arrival") or next_stop.get("departure"))
    eta_min = next_sched_arr_min + delay_minutes
    eta_str = _minutes_to_time_str(eta_min)

    journey_pct = int(round((curr_idx / max(1, total_stops - 1)) * 100))
    total_est_dist = max(350, total_stops * 95)
    travelled_est_dist = int(round(total_est_dist * (journey_pct / 100.0)))

    # Construct Station Timeline
    timeline: List[TrainStop] = []
    for i, s in enumerate(stops_data):
        has_passed = i <= curr_idx
        sched_arr = s.get("arrival")
        sched_dep = s.get("departure")
        
        act_arr = None
        act_dep = None
        if sched_arr and sched_arr.lower() != "none":
            act_arr = _minutes_to_time_str(_time_str_to_minutes(sched_arr) + (delay_minutes if has_passed else 0))
        if sched_dep and sched_dep.lower() != "none":
            act_dep = _minutes_to_time_str(_time_str_to_minutes(sched_dep) + (delay_minutes if has_passed else 0))

        timeline.append(
            TrainStop(
                station_code=s["station_code"],
                station_name=s["station_name"],
                arrival=sched_arr,
                departure=sched_dep,
                day=s.get("day", 1),
                stop_sequence=s.get("stop_sequence", i + 1),
                distance_km=int(round(i * (total_est_dist / max(1, total_stops - 1)))),
                delay_minutes=delay_minutes if has_passed else 0,
                actual_arrival=act_arr,
                actual_departure=act_dep,
                has_passed=has_passed,
            )
        )

    status_obj = TrainLiveStatus(
        train_number=clean_num,
        train_name=train_name,
        current_station=curr_stop["station_code"],
        current_station_name=curr_stop["station_name"],
        delay_minutes=delay_minutes,
        delay_status=delay_status,
        delay_trend=delay_trend,
        next_stop=next_stop["station_code"],
        next_stop_name=next_stop["station_name"],
        eta=eta_str,
        journey_percent=journey_pct,
        distance_travelled_km=travelled_est_dist,
        total_distance_km=total_est_dist,
        station_timeline=timeline,
        updated_at="Just now",
        source="ml_telemetry_engine",
        cached=False,
    )

    # 5. Store in Redis Cache (60-second TTL)
    try:
        redis = get_redis()
        await redis.set(cache_key, status_obj.model_dump_json(), ex=60)
    except Exception:
        pass

    return status_obj


async def get_train_schedule(train_number: str) -> TrainScheduleResponse:
    """Retrieve full station timetable for a train via active RailwayGateway."""
    from app.services.gateway import get_railway_gateway
    return await get_railway_gateway().get_train_schedule(train_number)

    train_name = stops_data[0].get("train_name", f"Express {clean_num}")
    origin_code = stops_data[0]["station_code"]
    dest_code = stops_data[-1]["station_code"]

    stops = [
        TrainStop(
            station_code=s["station_code"],
            station_name=s["station_name"],
            arrival=s.get("arrival"),
            departure=s.get("departure"),
            day=s.get("day", 1),
            stop_sequence=s.get("stop_sequence", idx + 1),
            distance_km=int(round(idx * 75)),
            delay_minutes=0,
            has_passed=False,
        )
        for idx, s in enumerate(stops_data)
    ]

    return TrainScheduleResponse(
        train_number=clean_num,
        train_name=train_name,
        origin_station=origin_code,
        destination_station=dest_code,
        total_stops=len(stops),
        stops=stops,
    )
