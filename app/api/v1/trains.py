"""Train status and schedule endpoints."""

from fastapi import APIRouter, HTTPException, Path
from app.schemas.train import TrainLiveStatus

router = APIRouter()


@router.get("/trains/{train_number}/live", response_model=TrainLiveStatus)
async def get_live_train_status(
    train_number: str = Path(..., description="5-digit Indian Railway train number, e.g. 12627"),
):
    """Fetch live running status and current delay for a train."""
    # Placeholder returning sample live format; will connect to rscfoss API in Phase 4
    return TrainLiveStatus(
        train_number=train_number,
        train_name="Karnataka Express",
        current_station="BINA",
        delay_minutes=25,
        next_stop="BPL",
        eta="14:15",
        updated_at="Just now",
    )
