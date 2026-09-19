"""Train and schedule schemas."""

from typing import Optional
from pydantic import BaseModel, Field


class TrainStop(BaseModel):
    station_code: str
    station_name: str
    arrival: Optional[str] = None
    departure: Optional[str] = None
    day: int = 1
    stop_sequence: Optional[int] = None


class TrainLiveStatus(BaseModel):
    train_number: str
    train_name: Optional[str] = None
    current_station: Optional[str] = None
    delay_minutes: int = 0
    next_stop: Optional[str] = None
    eta: Optional[str] = None
    updated_at: Optional[str] = None
