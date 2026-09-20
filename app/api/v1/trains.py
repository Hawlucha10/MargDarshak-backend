"""Train status and schedule endpoints."""

from fastapi import APIRouter, HTTPException, Path

from app.schemas.train import TrainLiveStatus, TrainScheduleResponse
from app.services.live_train_service import (
    get_live_train_status as service_get_live_status,
    get_train_schedule as service_get_schedule,
)

router = APIRouter()


@router.get("/trains/{train_number}/live", response_model=TrainLiveStatus)
async def get_live_train_status(
    train_number: str = Path(..., description="5-digit Indian Railway train number, e.g. 12627"),
):
    """
    Fetch live running telemetry, current delay, delay trend, and station progress.
    Backed by PostGIS timetable schedules, ML delay predictions, and 60s Redis caching.
    """
    clean_num = train_number.strip()
    if not clean_num:
        raise HTTPException(status_code=400, detail="Invalid train number")
    return await service_get_live_status(clean_num)


@router.get("/trains/{train_number}/schedule", response_model=TrainScheduleResponse)
async def get_train_schedule(
    train_number: str = Path(..., description="5-digit Indian Railway train number, e.g. 12627"),
):
    """
    Fetch full ordered station timetable stops for a train from PostGIS database.
    """
    clean_num = train_number.strip()
    if not clean_num:
        raise HTTPException(status_code=400, detail="Invalid train number")
    return await service_get_schedule(clean_num)
