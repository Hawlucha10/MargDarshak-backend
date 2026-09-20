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
from app.services.availability_service import (
    check_route_availability as service_check_route_availability,
    get_train_seat_availability as service_get_train_availability,
)

router = APIRouter()


@router.post("/availability/train", response_model=TrainAvailabilityResponse)
async def check_train_availability(payload: TrainAvailabilityRequest):
    """
    Tier-2 Real-Time Seat Availability Check for a specific train and corridor.
    Calculates class-wise berth status, Bayesian waitlist confirmation probabilities,
    and scans upstream stations for cross-quota arbitrage opportunities.
    """
    return await service_get_train_availability(
        train_number=payload.train_number,
        from_station=payload.from_station,
        to_station=payload.to_station,
        travel_date=payload.travel_date,
        quota=payload.quota,
    )


@router.get("/availability/train/{train_number}", response_model=TrainAvailabilityResponse)
async def get_train_availability_get(
    train_number: str = Path(..., description="5-digit Indian Railway train number, e.g. 12627"),
    from_station: str = Query(..., description="Origin station code, e.g. GWL"),
    to_station: str = Query(..., description="Destination station code, e.g. PUNE"),
    travel_date: str = Query(..., description="Date of travel (YYYY-MM-DD)"),
    quota: str = Query(default="GN", description="Booking quota: GN, TQ, etc."),
):
    """
    Convenience GET endpoint for checking single-train multi-class availability.
    """
    return await service_get_train_availability(
        train_number=train_number,
        from_station=from_station,
        to_station=to_station,
        travel_date=travel_date,
        quota=quota,
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
    return await service_check_route_availability(payload)
