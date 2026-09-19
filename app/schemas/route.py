"""Route search request and response schemas."""

from typing import List, Optional
from pydantic import BaseModel, Field


class RouteSearchRequest(BaseModel):
    origin: str = Field(..., description="Origin station code (e.g. GWL)", max_length=10)
    destination: str = Field(..., description="Destination station code (e.g. PUNE)", max_length=10)
    travel_date: str = Field(..., description="Date of travel (YYYY-MM-DD)")
    max_transfers: int = Field(default=2, ge=0, le=3, description="Maximum train changes (0 to 3)")
    priority: str = Field(default="balanced", description="Optimization priority: fastest, cheapest, balanced, reliable")


class TrainLeg(BaseModel):
    train_number: str
    train_name: str
    from_station: str
    from_station_name: str
    to_station: str
    to_station_name: str
    departure_time: str
    arrival_time: str
    day: int = 1
    predicted_delay_min: int = 0
    fare_estimate: Optional[int] = None


class TransferConnection(BaseModel):
    station_code: str
    station_name: str
    wait_time_minutes: int
    is_safe: bool = True
    delay_risk_warning: Optional[str] = None


class JourneyRoute(BaseModel):
    label: str = Field(..., description="Pareto tag, e.g. FASTEST, CHEAPEST, BALANCED, MOST_RELIABLE")
    total_travel_time: str
    total_fare: Optional[int] = None
    transfers: int
    reliability_score: float = Field(..., ge=0.0, le=1.0)
    legs: List[TrainLeg]
    transfers_info: List[TransferConnection] = []
    fare_arbitrage_tip: Optional[str] = None


class RouteSearchResponse(BaseModel):
    search_id: str
    origin: str
    destination: str
    travel_date: str
    total_routes_found: int
    routes: List[JourneyRoute]
    cached: bool = False
    computed_in_ms: float
