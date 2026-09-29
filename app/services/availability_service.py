import asyncio
import datetime
import json
import math
from typing import Any, Dict, List, Optional, Tuple

import httpx

from app.config import get_settings
from app.core.demand_buffer import get_demand_adaptive_buffer
from app.core.quota_arbitrage import find_cross_quota_arbitrage
from app.db.redis_client import get_redis
from app.schemas.availability import (
    ClassAvailabilityInfo,
    LegAvailabilityRequest,
    LegAvailabilityResult,
    QuotaArbitrageTip,
    RouteAvailabilityRequest,
    RouteAvailabilityResponse,
    TrainAvailabilityRequest,
    TrainAvailabilityResponse,
)
from app.services.live_train_service import fetch_train_stops_db, _generate_fallback_stops


def _calculate_class_fares(distance_km: int) -> Dict[str, int]:
    """
    Calculate Indian Railways telescopic distance-slab fares across classes.
    """
    d = max(50, distance_km)
    if d > 1200:
        dist_factor = 0.82
    elif d > 800:
        dist_factor = 0.88
    elif d > 500:
        dist_factor = 0.94
    else:
        dist_factor = 1.0

    fares = {
        "2S": int(round((0.35 * d * dist_factor) + 45)),
        "SL": int(round((0.55 * d * dist_factor) + 120)),
        "3E": int(round((1.30 * d * dist_factor) + 280)),
        "3A": int(round((1.45 * d * dist_factor) + 340)),
        "2A": int(round((2.10 * d * dist_factor) + 480)),
        "1A": int(round((3.55 * d * dist_factor) + 750)),
        "CC": int(round((1.20 * d * dist_factor) + 220)),
    }
    return fares


def _format_date_for_api(date_str: str) -> str:
    """Ensure date is in DD-MM-YYYY format expected by RapidAPI."""
    try:
        if "-" in date_str:
            parts = date_str.split("-")
            if len(parts[0]) == 4:  # YYYY-MM-DD -> DD-MM-YYYY
                return f"{parts[2]}-{parts[1]}-{parts[0]}"
    except Exception:
        pass
    return date_str


async def _fetch_railkit_availability(
    train_number: str,
    source: str,
    destination: str,
    travel_date: str,
    class_type: str = "SL",
    quota: str = "GN",
) -> Tuple[bool, Optional[Any], Optional[str]]:
    """
    Calls the RailKit RapidAPI endpoint:
    GET https://railkit-indian-railway-data.p.rapidapi.com/api/getAvailability/{train}/{from}/{to}/{date}/{class}/{quota}
    """
    settings = get_settings()
    if not settings.rapidapi_key:
        return False, None, "RapidAPI key not configured."

    formatted_date = _format_date_for_api(travel_date)
    clean_train = train_number.strip()
    clean_from = source.upper().strip()
    clean_to = destination.upper().strip()
    clean_class = class_type.upper().strip() if class_type else "SL"
    clean_quota = quota.upper().strip() if quota else "GN"

    url = f"https://{settings.rapidapi_host}/api/getAvailability/{clean_train}/{clean_from}/{clean_to}/{formatted_date}/{clean_class}/{clean_quota}"

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
                return False, None, "RapidAPI monthly quota limit reached."
            else:
                return False, None, f"HTTP {resp.status_code}"
    except Exception as e:
        return False, None, str(e)


async def get_train_seat_availability(
    train_number: str,
    from_station: str,
    to_station: str,
    travel_date: str,
    quota: str = "GN",
    travel_class: str = "SL",
) -> TrainAvailabilityResponse:
    """Retrieve seat availability via the active RailwayGateway (Digital Twin or CRIS Production)."""
    from app.services.gateway import get_railway_gateway
    return await get_railway_gateway().get_train_seat_availability(
        train_number, from_station, to_station, travel_date, quota, travel_class
    )


async def _direct_railkit_train_availability(
    train_number: str,
    from_station: str,
    to_station: str,
    travel_date: str,
    quota: str = "GN",
    travel_class: str = "SL",
) -> TrainAvailabilityResponse:
    """Direct RailKit RapidAPI caller."""
    import re

    clean_num = train_number.strip()
    from_code = from_station.upper().strip()
    to_code = to_station.upper().strip()
    clean_quota = quota.upper().strip()
    clean_class = travel_class.upper().strip() if travel_class else "SL"
    formatted_date = _format_date_for_api(travel_date)

    cache_key = f"avail:{clean_num}:{from_code}:{to_code}:{travel_date}:{clean_class}:{clean_quota}"

    # 1. Redis Cache Check (600-second TTL to conserve user quota)
    try:
        redis = get_redis()
        cached_data = await redis.get(cache_key)
        if cached_data:
            data = json.loads(cached_data)
            data["cached"] = True
            return TrainAvailabilityResponse(**data)
    except Exception:
        pass

    # 2. Fetch train details
    stops_data = await fetch_train_stops_db(clean_num)
    if not stops_data:
        stops_data = _generate_fallback_stops(clean_num)

    train_name = stops_data[0].get("train_name", f"Express {clean_num}") if stops_data else f"Express {clean_num}"

    # 3. Call RailKit RapidAPI
    api_success, api_data, error_msg = await _fetch_railkit_availability(
        train_number=clean_num,
        source=from_code,
        destination=to_code,
        travel_date=travel_date,
        class_type=clean_class,
        quota=clean_quota,
    )

    classes_output: List[ClassAvailabilityInfo] = []

    # Attempt to parse classes from live API response if available
    if api_success and api_data:
        # Dedicated handler for RailKit structure:
        # {"success": true, "data": {"train": ..., "fare": ..., "availability": [...]}}
        if isinstance(api_data, dict) and api_data.get("success") is True and isinstance(api_data.get("data"), dict):
            data_dict = api_data["data"]
            if "availability" in data_dict:
                train_meta = data_dict.get("train", {})
                fare_meta = data_dict.get("fare", {})
                if train_meta.get("trainName"):
                    train_name = train_meta["trainName"]
                t_fare = int(fare_meta.get("totalFare") or fare_meta.get("baseFare") or 0)
                t_class = str(train_meta.get("travelClass") or clean_class)
                avail_items = data_dict.get("availability", [])

                if isinstance(avail_items, list) and avail_items:
                    chosen_entry = avail_items[0]
                    for a_item in avail_items:
                        if isinstance(a_item, dict) and (formatted_date in str(a_item.get("date", "")) or str(a_item.get("date", "")) in formatted_date):
                            chosen_entry = a_item
                            break

                    disp_status = str(chosen_entry.get("availabilityText") or chosen_entry.get("rawStatus") or chosen_entry.get("status") or "AVAILABLE")
                    if chosen_entry.get("rawStatus") and chosen_entry.get("availabilityText"):
                        disp_status = f"{chosen_entry['availabilityText']} ({chosen_entry['rawStatus']})"
                    elif chosen_entry.get("availabilityText"):
                        disp_status = chosen_entry["availabilityText"]

                    is_avbl = "AVAILABLE" in disp_status.upper() or "CURR_AVBL" in disp_status.upper()

                    pred_pct = chosen_entry.get("predictionPercentage")
                    pred_str = chosen_entry.get("prediction")
                    if pred_pct is not None:
                        conf_prob = float(pred_pct) / 100.0
                        conf_str = pred_str or f"{int(pred_pct)}%"
                    elif is_avbl:
                        conf_prob = 1.0
                        conf_str = "100%"
                    else:
                        conf_prob = 0.5
                        conf_str = "50%"

                    nums = re.findall(r'\d+', disp_status)
                    seats = int(nums[-1]) if nums else 0

                    classes_output.append(
                        ClassAvailabilityInfo(
                            class_code=t_class,
                            class_name=f"Class {t_class}",
                            status=disp_status,
                            available_seats=seats,
                            fare_inr=t_fare,
                            confirmation_probability=conf_prob,
                            confirmation_probability_pct=conf_str,
                            is_available=is_avbl,
                        )
                    )

        target_data = api_data
        if not classes_output and isinstance(api_data, dict) and "data" in api_data and api_data["data"] is not None:
            target_data = api_data["data"]

        # Fallback Case A: target_data is a list (e.g. date-wise or class-wise entries)
        if not classes_output and isinstance(target_data, list):
            for entry in target_data:
                if not isinstance(entry, dict):
                    continue
                e_status = str(entry.get("status") or entry.get("availability") or entry.get("current_status") or "AVAILABLE")
                e_fare = int(entry.get("fare") or entry.get("total_fare") or 0)
                e_class = str(entry.get("class") or entry.get("class_type") or clean_class)
                is_avbl = "AVAILABLE" in e_status.upper() or "CURR_AVBL" in e_status.upper()
                nums = re.findall(r'\d+', e_status)
                seats = int(nums[-1]) if nums else 0
                classes_output.append(
                    ClassAvailabilityInfo(
                        class_code=e_class,
                        class_name=f"Class {e_class}",
                        status=e_status,
                        available_seats=seats,
                        fare_inr=e_fare,
                        confirmation_probability=1.0 if is_avbl else 0.5,
                        confirmation_probability_pct="100%" if is_avbl else "50%",
                        is_available=is_avbl,
                    )
                )
        # Fallback Case B: target_data is a dictionary
        elif not classes_output and isinstance(target_data, dict):
            e_status = str(target_data.get("status") or target_data.get("availability") or target_data.get("current_status") or "")
            if e_status:
                e_fare = int(target_data.get("fare") or target_data.get("total_fare") or 0)
                e_class = str(target_data.get("class") or target_data.get("class_type") or clean_class)
                is_avbl = "AVAILABLE" in e_status.upper() or "CURR_AVBL" in e_status.upper()
                nums = re.findall(r'\d+', e_status)
                seats = int(nums[-1]) if nums else 0
                classes_output.append(
                    ClassAvailabilityInfo(
                        class_code=e_class,
                        class_name=f"Class {e_class}",
                        status=e_status,
                        available_seats=seats,
                        fare_inr=e_fare,
                        confirmation_probability=1.0 if is_avbl else 0.5,
                        confirmation_probability_pct="100%" if is_avbl else "50%",
                        is_available=is_avbl,
                    )
                )



    # 4. If no live data from API: Do NOT generate fake/simulated fallback!
    # Direct user clearly to IRCTC official website.
    if not classes_output:
        irctc_url = f"https://www.irctc.co.in/nget/train-search"
        response = TrainAvailabilityResponse(
            train_number=clean_num,
            train_name=train_name,
            from_station=from_code,
            to_station=to_code,
            travel_date=travel_date,
            quota=clean_quota,
            classes=[],
            arbitrage_recommendation=None,
            cached=False,
            checked_at=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            api_status="unavailable",
            message="Live seat availability via API is currently unavailable. You can check real-time availability and book directly on the official IRCTC website.",
            irctc_url=irctc_url,
        )
        try:
            redis = get_redis()
            await redis.set(cache_key, response.model_dump_json(), ex=120)
        except Exception:
            pass
        return response

    response = TrainAvailabilityResponse(
        train_number=clean_num,
        train_name=train_name,
        from_station=from_code,
        to_station=to_code,
        travel_date=travel_date,
        quota=clean_quota,
        classes=classes_output,
        arbitrage_recommendation=None,
        cached=False,
        checked_at=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        api_status="success",
        message=None,
        irctc_url="https://www.irctc.co.in/nget/train-search",
    )

    try:
        redis = get_redis()
        await redis.set(cache_key, response.model_dump_json(), ex=300)
    except Exception:
        pass

    return response


async def check_route_availability(request: RouteAvailabilityRequest) -> RouteAvailabilityResponse:
    """Audit route availability via the active RailwayGateway (Digital Twin or CRIS Production)."""
    from app.services.gateway import get_railway_gateway
    return await get_railway_gateway().check_route_availability(request)


async def _direct_railkit_route_availability(request: RouteAvailabilityRequest) -> RouteAvailabilityResponse:
    """Direct RailKit RapidAPI route checker."""
    cache_key = f"route:avail:{request.route_id}"

    # 1. Redis Cache Check
    try:
        redis = get_redis()
        cached_data = await redis.get(cache_key)
        if cached_data:
            data = json.loads(cached_data)
            data["cached"] = True
            return RouteAvailabilityResponse(**data)
    except Exception:
        pass

    # 2. Check all legs concurrently
    tasks = [
        get_train_seat_availability(
            train_number=leg.train_number,
            from_station=leg.from_station,
            to_station=leg.to_station,
            travel_date=leg.travel_date,
            quota=leg.quota,
            travel_class=leg.travel_class,
        )
        for leg in request.legs
    ]

    leg_responses: List[TrainAvailabilityResponse] = await asyncio.gather(*tasks)

    legs_results: List[LegAvailabilityResult] = []
    total_fare = 0
    all_confirmed = True
    any_available = False
    advisories: List[str] = []

    for req_leg, avail_res in zip(request.legs, leg_responses):
        matching_class = next(
            (c for c in avail_res.classes if c.class_code == req_leg.travel_class),
            avail_res.classes[0] if avail_res.classes else None,
        )

        if matching_class:
            any_available = True
            fare = matching_class.fare_inr
            status = matching_class.status
            seats = matching_class.available_seats
            is_conf = matching_class.is_available
            conf_prob = matching_class.confirmation_probability
            if not is_conf:
                all_confirmed = False
        else:
            fare = 0
            status = "UNAVAILABLE VIA API"
            seats = 0
            is_conf = False
            conf_prob = None
            all_confirmed = False

        total_fare += fare

        legs_results.append(
            LegAvailabilityResult(
                train_number=req_leg.train_number,
                train_name=avail_res.train_name,
                from_station=req_leg.from_station,
                to_station=req_leg.to_station,
                travel_class=req_leg.travel_class,
                quota=req_leg.quota,
                status=status,
                seats=seats,
                fare_inr=fare,
                confirmation_probability=conf_prob,
                is_confirmed=is_conf,
                quota_arbitrage=None,
                classes=avail_res.classes,
                api_status=avail_res.api_status,
                message=avail_res.message,
                irctc_url=avail_res.irctc_url,
            )
        )

    # 3. Assess Route Level Status
    if not any_available:
        risk_label = "UNAVAILABLE VIA API"
        api_st = "unavailable"
        msg = "Live seat availability via API is currently unavailable. You can check each leg on the official IRCTC website."
        advisories.append("Live seat availability via API is currently unavailable.")
        advisories.append("Please verify seat availability and book each leg on the official IRCTC website: https://www.irctc.co.in/nget/train-search")
    elif all_confirmed:
        risk_label = "LOW RISK - 100% Confirmed Berths"
        api_st = "success"
        msg = None
    else:
        risk_label = "MODERATE RISK - Check Waitlist on IRCTC"
        api_st = "partial"
        msg = "Some legs may have limited availability. Please verify berths on the official IRCTC website before traveling."
        advisories.append("One or more legs are waitlisted. Please verify status on IRCTC: https://www.irctc.co.in/nget/train-search")

    response = RouteAvailabilityResponse(
        route_id=request.route_id,
        is_fully_confirmed=all_confirmed if any_available else False,
        overall_confirmation_risk=risk_label,
        total_fare_inr=total_fare,
        legs=legs_results,
        advisories=advisories,
        advisory_notes=advisories,
        cached=False,
        api_status=api_st,
        message=msg,
        irctc_url="https://www.irctc.co.in/nget/train-search",
        joint_confirmation_pct="100%" if (any_available and all_confirmed) else None,
        joint_confirmation_prob=1.0 if (any_available and all_confirmed) else None,
    )

    try:
        redis = get_redis()
        await redis.set(cache_key, response.model_dump_json(), ex=120)
    except Exception:
        pass

    return response

