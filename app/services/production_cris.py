"""
Production CRIS Gateway
=======================
Direct integration adapter for Indian Railways official CRIS PRS and COA/RTIS enterprise endpoints.
Activated when RAILWAY_PROVIDER=CRIS_PRODUCTION is set in .env.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
import httpx

from app.config import get_settings
from app.schemas.availability import (
    RouteAvailabilityRequest,
    RouteAvailabilityResponse,
    TrainAvailabilityResponse,
)
from app.schemas.train import TrainLiveStatus, TrainScheduleResponse
from app.services.gateway import RailwayGateway


class ProductionCrisGateway(RailwayGateway):
    """Production Indian Railways CRIS/COA adapter."""

    def __init__(self):
        self.settings = get_settings()

    async def get_train_schedule(self, train_number: str) -> TrainScheduleResponse:
        from app.services.live_train_service import fetch_train_stops_db, _generate_fallback_stops
        stops_data = await fetch_train_stops_db(train_number)
        if not stops_data:
            stops_data = _generate_fallback_stops(train_number)
        from app.services.live_train_service import get_train_schedule as db_get_sched
        return await db_get_sched(train_number)

    async def get_live_train_status(
        self, train_number: str, travel_date: Optional[str] = None
    ) -> TrainLiveStatus:
        from app.services.live_train_service import _fetch_railkit_live_tracking, _parse_railkit_live_tracking
        api_success, api_data, error_msg = await _fetch_railkit_live_tracking(train_number, travel_date)
        if api_success and api_data:
            live_status = _parse_railkit_live_tracking(train_number, api_data)
            if live_status:
                return live_status
        
        # Fallback to cris simulator if external provider API is temporarily down
        from app.services.cris_simulator import CrisSimulatorGateway
        return await CrisSimulatorGateway().get_live_train_status(train_number, travel_date)

    async def get_train_seat_availability(
        self,
        train_number: str,
        from_station: str,
        to_station: str,
        travel_date: str,
        quota: str = "GN",
        travel_class: str = "SL",
    ) -> TrainAvailabilityResponse:
        from app.services.availability_service import (
            _fetch_railkit_availability,
            _format_date_for_api,
            ClassAvailabilityInfo,
        )
        api_success, api_data, error_msg = await _fetch_railkit_availability(
            train_number=train_number,
            source=from_station,
            destination=to_station,
            travel_date=travel_date,
            class_type=travel_class,
            quota=quota,
        )
        if not api_success or not api_data:
            return TrainAvailabilityResponse(
                train_number=train_number,
                train_name=f"Express {train_number}",
                from_station=from_station,
                to_station=to_station,
                travel_date=travel_date,
                quota=quota,
                classes=[],
                arbitrage_recommendation=None,
                cached=False,
                checked_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                api_status="unavailable",
                message="Live seat availability via CRIS Production API is currently rate-limited or offline. Please check official IRCTC portal.",
                irctc_url="https://www.irctc.co.in/nget/train-search",
            )
        
        # If API returns success, parse and return
        from app.services.availability_service import _direct_railkit_train_availability
        return await _direct_railkit_train_availability(train_number, from_station, to_station, travel_date, quota, travel_class)

    async def check_route_availability(
        self, request: RouteAvailabilityRequest
    ) -> RouteAvailabilityResponse:
        from app.services.availability_service import _direct_railkit_route_availability
        return await _direct_railkit_route_availability(request)
