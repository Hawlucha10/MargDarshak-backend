"""
Real-Time Seat Availability and Quota Arbitrage API Endpoints.
Milestone 4: Two-Tier Real-Time Verification Layer.
"""

from fastapi import APIRouter, HTTPException, Query, Path

from app.schemas.availability import (
    RouteAvailabilityRequest,
    RouteAvailabilityResponse,
    TrainAvailabilityRequest,
    TrainAvailabilityResponse,
)
from app.services.gateway import get_railway_gateway

router = APIRouter()


@router.post("/availability/train", response_model=TrainAvailabilityResponse)
async def check_train_availability(payload: TrainAvailabilityRequest):
    """
    Tier-2 Real-Time Seat Availability Check for a specific train and corridor.
    Routed through pluggable RailwayGateway (Digital Twin or Production CRIS).
    """
    gateway = get_railway_gateway()
    return await gateway.get_train_seat_availability(
        train_number=payload.train_number,
        from_station=payload.from_station,
        to_station=payload.to_station,
        travel_date=payload.travel_date,
        quota=payload.quota,
        travel_class=payload.travel_class,
    )


@router.get("/availability/train/{train_number}", response_model=TrainAvailabilityResponse)
async def get_train_availability_get(
    train_number: str = Path(..., description="5-digit Indian Railway train number, e.g. 12627"),
    from_station: str = Query(..., description="Origin station code, e.g. GWL"),
    to_station: str = Query(..., description="Destination station code, e.g. PUNE"),
    travel_date: str = Query(..., description="Date of travel (YYYY-MM-DD)"),
    quota: str = Query(default="GN", description="Booking quota: GN, TQ, etc."),
    travel_class: str = Query(default="SL", description="Railway class code: SL, 3A, 2A, 1A, etc."),
):
    """
    Convenience GET endpoint for checking single-train multi-class availability.
    """
    gateway = get_railway_gateway()
    return await gateway.get_train_seat_availability(
        train_number=train_number,
        from_station=from_station,
        to_station=to_station,
        travel_date=travel_date,
        quota=quota,
        travel_class=travel_class,
    )



@router.post("/availability/route", response_model=RouteAvailabilityResponse)
async def check_route_journey_availability(payload: RouteAvailabilityRequest):
    """
    Evaluates end-to-end trip booking feasibility across all legs of a multi-hop journey.
    Concurrently checks availability for every leg, computes joint connection risk,
    and identifies quota arbitrage options for any waitlisted connection.
    """
    if not payload.legs:
        raise HTTPException(status_code=400, detail="At least one train leg is required")
    gateway = get_railway_gateway()
    return await gateway.check_route_availability(payload)
