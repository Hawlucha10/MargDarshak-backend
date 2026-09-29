"""Train status and schedule endpoints."""

from fastapi import APIRouter, HTTPException, Path

from app.schemas.train import TrainLiveStatus, TrainScheduleResponse
from app.services.gateway import get_railway_gateway

router = APIRouter()


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
