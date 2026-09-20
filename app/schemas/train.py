"""Train and schedule schemas for live tracking and timetable inspection."""

from typing import List, Optional
from pydantic import BaseModel, Field


class TrainStop(BaseModel):
    station_code: str
    station_name: str
    arrival: Optional[str] = None
    departure: Optional[str] = None
    day: int = 1
    stop_sequence: Optional[int] = None
    distance_km: Optional[int] = None
    delay_minutes: int = 0
    actual_arrival: Optional[str] = None
    actual_departure: Optional[str] = None
    has_passed: bool = False


class TrainLiveStatus(BaseModel):
    train_number: str
    train_name: str
    current_station: str
    current_station_name: str
    delay_minutes: int = 0
    delay_status: str = Field(
        default="ON TIME",
        description="Operational category: ON TIME, SLIGHT DELAY, MODERATE DELAY, or CRITICAL DELAY",
    )
    delay_trend: str = Field(
        default="stable",
        description="Telemetry trend: recovering (making up time), stable, or accumulating delay",
    )
    next_stop: str
    next_stop_name: str
    eta: str
    journey_percent: int = Field(default=0, ge=0, le=100, description="Percentage of full route completed")
    distance_travelled_km: Optional[int] = None
    total_distance_km: Optional[int] = None
    station_timeline: List[TrainStop] = []
    updated_at: str = "Just now"
    source: str = "ml_telemetry_engine"
    cached: bool = False


class TrainScheduleResponse(BaseModel):
    train_number: str
    train_name: str
    origin_station: str
    destination_station: str
    total_stops: int
    stops: List[TrainStop]
