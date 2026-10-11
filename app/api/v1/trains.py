"""Train status, schedule, and ML delay prediction endpoints."""

from datetime import datetime, timezone, timedelta
from typing import Optional
from fastapi import APIRouter, HTTPException, Path, Query

from app.ml.delay_predictor import get_predictor
from app.schemas.train import (
    EnsembleDetail,
    TrainDelayPredictionResponse,
    TrainLiveStatus,
    TrainScheduleResponse,
)
from app.services.gateway import get_railway_gateway

router = APIRouter()
IST = timezone(timedelta(hours=5, minutes=30))


@router.get("/trains/{train_number}/live", response_model=TrainLiveStatus)
async def get_live_train_status(
    train_number: str = Path(..., description="5-digit Indian Railway train number, e.g. 12627"),
):
    """
    Fetch live running telemetry, current delay, delay trend, and station progress.
    Routed through pluggable RailwayGateway (Digital Twin or Production CRIS).
    """
    clean_num = train_number.strip()
    if not clean_num:
        raise HTTPException(status_code=400, detail="Invalid train number")
    gateway = get_railway_gateway()
    return await gateway.get_live_train_status(clean_num)


@router.get("/trains/{train_number}/schedule", response_model=TrainScheduleResponse)
async def get_train_schedule(
    train_number: str = Path(..., description="5-digit Indian Railway train number, e.g. 12627"),
):
    """
    Fetch full ordered station timetable stops for a train.
    Routed through pluggable RailwayGateway (Digital Twin or Production CRIS).
    """
    clean_num = train_number.strip()
    if not clean_num:
        raise HTTPException(status_code=400, detail="Invalid train number")
    gateway = get_railway_gateway()
    return await gateway.get_train_schedule(clean_num)


@router.get("/trains/{train_number}/delay", response_model=TrainDelayPredictionResponse)
async def get_train_delay_prediction(
    train_number: str = Path(..., description="5-digit Indian Railway train number, e.g. 12627"),
    travel_date: Optional[str] = Query(None, description="Date of travel (YYYY-MM-DD)"),
    departure_hour: Optional[int] = Query(None, ge=0, le=23, description="Departure hour (0-23)"),
    zone: Optional[str] = Query(None, description="Operating zone (e.g. NR, NCR, CR, SWR)"),
    distance_km: Optional[int] = Query(None, description="Total journey distance in km"),
):
    """
    Fetch full Tri-Model ML Ensemble delay prediction, P85 quantile buffer,
    probability breakdown (XGBoost + LightGBM + CatBoost + Meta-Learner), and risk explanations.
    """
    clean_num = train_number.strip()
    if not clean_num:
        raise HTTPException(status_code=400, detail="Invalid train number")

    gateway = get_railway_gateway()
    train_name = f"Train {clean_num}"
    calc_distance = distance_km
    calc_zone = zone or "NR"

    try:
        sched = await gateway.get_train_schedule(clean_num)
        if sched and sched.stops:
            train_name = sched.train_name
            if not calc_distance and sched.stops[-1].distance_km:
                calc_distance = sched.stops[-1].distance_km
            if not zone and hasattr(sched.stops[0], "zone"):
                calc_zone = getattr(sched.stops[0], "zone", "NR")
    except Exception:
        pass

    now_ist = datetime.now(IST)
    if travel_date:
        try:
            t_dt = datetime.strptime(travel_date.strip(), "%Y-%m-%d")
            month_val = t_dt.month
            day_of_week_val = t_dt.weekday()
        except Exception:
            month_val = now_ist.month
            day_of_week_val = now_ist.weekday()
    else:
        month_val = now_ist.month
        day_of_week_val = now_ist.weekday()

    dep_hour = departure_hour if departure_hour is not None else 8
    dist = calc_distance or 650

    predictor = get_predictor()
    pred = predictor.predict_delay(
        train_number=clean_num,
        month=month_val,
        day_of_week=day_of_week_val,
        departure_hour=dep_hour,
        zone=calc_zone,
        distance_km=dist,
    )

    ens_detail = None
    if "ensemble_detail" in pred:
        ens_detail = EnsembleDetail(**pred["ensemble_detail"])

    return TrainDelayPredictionResponse(
        train_number=clean_num,
        train_name=train_name,
        predicted_delay_minutes=pred["predicted_delay_minutes"],
        p85_delay_buffer_minutes=pred["p85_delay_buffer_minutes"],
        delay_probability=pred["delay_probability"],
        risk_level=pred["risk_level"],
        explanations=pred["explanations"],
        safe_transfer_buffer_minutes=pred["safe_transfer_buffer_minutes"],
        model_version=pred.get("model_version", "ensemble_v3_p85"),
        ensemble_detail=ens_detail,
        cached=False,
    )
