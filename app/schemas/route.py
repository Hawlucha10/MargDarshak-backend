"""Route search request and response schemas with multimodal bus support."""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class RouteSearchRequest(BaseModel):
    origin: str = Field(..., description="Origin station code (e.g. GWL)", max_length=10)
    destination: str = Field(..., description="Destination station code (e.g. PUNE)", max_length=10)
    travel_date: str = Field(..., description="Date of travel (YYYY-MM-DD)")
    max_transfers: int = Field(default=2, ge=0, le=3, description="Maximum train changes (0 to 3)")
    priority: str = Field(default="balanced", description="Optimization priority: fastest, cheapest, balanced, reliable, comfort")
    accessible_only: bool = Field(default=False, description="Require 100% step-free wheelchair ramp accessibility")
    arrive_before_time: Optional[str] = Field(default=None, description="Deadline: arrive before this time (HH:MM format)")
    prefer_home_wait: bool = Field(default=False, description="Minimize intermediate station layover; wait at home instead")
    include_buses: bool = Field(default=True, description="Include multimodal bus alternatives for long layovers")


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
    departure_platform: Optional[str] = Field(default="PF 1", description="Departure platform number")
    arrival_platform: Optional[str] = Field(default="PF 2", description="Arrival platform number")
    mode: str = Field(default="TRAIN", description="Leg mode: TRAIN or BUS")
    from_lat: Optional[float] = None
    from_lon: Optional[float] = None
    to_lat: Optional[float] = None
    to_lon: Optional[float] = None


class BusLeg(BaseModel):
    """A bus leg within a multimodal journey."""
    operator_name: str
    operator_code: str
    bus_type: str
    from_terminal: str
    to_terminal: str
    from_station_code: str
    to_station_code: str
    departure_time: str
    arrival_time: str
    duration_minutes: int
    fare: int
    is_ac: bool = False
    rating: Optional[float] = None
    walk_to_terminal_min: int = 15
    walk_from_terminal_min: int = 15
    mode: str = Field(default="BUS")
    from_lat: Optional[float] = None
    from_lon: Optional[float] = None
    to_lat: Optional[float] = None
    to_lon: Optional[float] = None


class TransferConnection(BaseModel):
    station_code: str
    station_name: str
    wait_time_minutes: int
    is_safe: bool = True
    delay_risk_warning: Optional[str] = None
    arrival_platform: Optional[str] = Field(default="PF 2", description="Arrival platform for incoming train")
    departure_platform: Optional[str] = Field(default="PF 4", description="Departure platform for connecting train")
    interchange_guide: Optional[str] = Field(
        default="Cross via Foot Overbridge (FOB) lift or ramp",
        description="Navigation guide between platforms",
    )
    bus_alternatives_count: int = Field(default=0, description="Number of bus alternatives from this station")


class JourneyRoute(BaseModel):
    label: str = Field(..., description="Pareto tag: FASTEST, CHEAPEST, BALANCED, MOST_RELIABLE, COMFORT_HOMESTAY, MULTIMODAL_FASTEST")
    total_travel_time: str
    total_fare: Optional[int] = None
    transfers: int
    reliability_score: float = Field(..., ge=0.0, le=1.0)
    joint_reliability_percent: Optional[str] = None
    legs: List[TrainLeg]
    bus_legs: List[BusLeg] = Field(default_factory=list, description="Bus legs in multimodal journeys")
    transfers_info: List[TransferConnection] = []
    fare_arbitrage_tip: Optional[str] = None
    accessibility_badge: Optional[str] = None
    weather_advisory: Optional[str] = None
    is_multimodal: bool = Field(default=False, description="True if route includes bus legs")
    time_saved_vs_train_minutes: Optional[int] = Field(default=None, description="Minutes saved by taking bus vs waiting for next train")
    comfort_score: Optional[float] = Field(default=None, description="Lower is better: Duration + 3x intermediate layover")


class RouteSearchResponse(BaseModel):
    search_id: str
    origin: str
    destination: str
    travel_date: str
    total_routes_found: int
    routes: List[JourneyRoute]
    cached: bool = False
    computed_in_ms: float
    nlp_query: Optional[str] = None
    nlp_interpretation: Optional[Dict[str, Any]] = None
    ai_summary: Optional[str] = None
