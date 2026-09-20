"""Pydantic schemas for Tier-2 Real-Time Seat Availability and Quota Arbitrage."""

from typing import List, Optional
from pydantic import BaseModel, Field


class TrainAvailabilityRequest(BaseModel):
    train_number: str = Field(..., description="5-digit Indian Railway train number, e.g. 12627")
    from_station: str = Field(..., description="Boarding station code, e.g. GWL", max_length=10)
    to_station: str = Field(..., description="Destination station code, e.g. PUNE", max_length=10)
    travel_date: str = Field(..., description="Date of travel (YYYY-MM-DD)")
    quota: str = Field(default="GN", description="Booking quota: GN (General), TQ (Tatkal), LD (Ladies)")


class ClassAvailabilityInfo(BaseModel):
    class_code: str = Field(..., description="Railway booking class, e.g. 1A, 2A, 3A, 3E, SL, CC, 2S")
    class_name: str = Field(..., description="Full class title, e.g. Sleeper Class, AC 3 Tier")
    status: str = Field(..., description="Status string: AVAILABLE, RAC, WL, or REGRET")
    available_seats: int = Field(default=0, description="Seats count if AVAILABLE, or queue number if WL/RAC")
    fare_inr: int = Field(..., description="Class ticket fare in Indian Rupees")
    confirmation_probability: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    confirmation_probability_pct: Optional[str] = None
    is_available: bool = Field(default=False, description="True if confirmed seats are immediately bookable")


class QuotaArbitrageTip(BaseModel):
    upstream_station_code: str
    upstream_station_name: str
    quota_type: str
    available_seats: int
    ticket_fare: int
    origin_fare: int
    savings_inr: int
    instruction: str


class TrainAvailabilityResponse(BaseModel):
    train_number: str
    train_name: str
    from_station: str
    to_station: str
    travel_date: str
    quota: str
    classes: List[ClassAvailabilityInfo]
    arbitrage_recommendation: Optional[QuotaArbitrageTip] = None
    cached: bool = False
    checked_at: str = "Just now"


class LegAvailabilityRequest(BaseModel):
    train_number: str
    train_name: Optional[str] = None
    from_station: str
    to_station: str
    travel_date: str
    travel_class: str = Field(default="SL", description="Requested class, e.g. SL, 3A, 2A")
    quota: str = Field(default="GN", description="Requested quota: GN, TQ")


class RouteAvailabilityRequest(BaseModel):
    route_id: str = Field(..., description="Identifier of the selected journey route")
    legs: List[LegAvailabilityRequest] = Field(..., min_length=1, description="Ordered train legs in the route")


class LegAvailabilityResult(BaseModel):
    train_number: str
    train_name: str
    from_station: str
    to_station: str
    travel_class: str
    quota: str
    status: str
    seats: int
    fare_inr: int
    confirmation_probability: Optional[float] = None
    is_confirmed: bool
    quota_arbitrage: Optional[QuotaArbitrageTip] = None


class RouteAvailabilityResponse(BaseModel):
    route_id: str
    is_fully_confirmed: bool
    overall_confirmation_risk: str
    total_fare_inr: int
    legs: List[LegAvailabilityResult]
    advisory_notes: List[str] = []
    cached: bool = False
