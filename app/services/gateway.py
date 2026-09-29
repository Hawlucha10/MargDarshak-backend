"""
Railway Gateway Abstraction Layer
=================================
Provides a pluggable adapter pattern decoupling MargDarshak from backend railway providers.

Supported Providers:
- CRIS_SIMULATOR: High-fidelity Indian Railways Digital Twin (WTT, COA/RTIS Physics, CRIS PRS Multi-Quota).
- CRIS_PRODUCTION: Real-world Indian Railways CRIS / COA / RapidAPI enterprise endpoints.

Switching between simulation and production is done via RAILWAY_PROVIDER in .env.
"""

from abc import ABC, abstractmethod
from functools import lru_cache
from typing import Optional

from app.config import get_settings
from app.schemas.availability import (
    RouteAvailabilityRequest,
    RouteAvailabilityResponse,
    TrainAvailabilityResponse,
)
from app.schemas.train import TrainLiveStatus, TrainScheduleResponse


class RailwayGateway(ABC):
    """Abstract interface defining all core railway telemetry and ticketing operations."""

    @abstractmethod
    async def get_train_schedule(self, train_number: str) -> TrainScheduleResponse:
        """Retrieve complete station stop sequence and scheduled arrival/departure times."""
        pass

    @abstractmethod
    async def get_live_train_status(
        self, train_number: str, travel_date: Optional[str] = None
    ) -> TrainLiveStatus:
        """Retrieve real-time GPS & COA/RTIS train running telemetry and delay state."""
        pass

    @abstractmethod
    async def get_train_seat_availability(
        self,
        train_number: str,
        from_station: str,
        to_station: str,
        travel_date: str,
        quota: str = "GN",
        travel_class: str = "SL",
    ) -> TrainAvailabilityResponse:
        """Retrieve multi-class PRS seat availability, waitlist probability, and quota arbitrage."""
        pass

    @abstractmethod
    async def check_route_availability(
        self, request: RouteAvailabilityRequest
    ) -> RouteAvailabilityResponse:
        """Audit multi-leg journey seat availability across all transfers concurrently."""
        pass


_gateway_instance: Optional[RailwayGateway] = None


def get_railway_gateway() -> RailwayGateway:
    """
    Factory function returning the active Railway Gateway implementation.
    Reads 'railway_provider' from application settings.
    """
    global _gateway_instance
    if _gateway_instance is None:
        settings = get_settings()
        provider = (settings.railway_provider or "CRIS_SIMULATOR").upper().strip()

        if provider == "CRIS_PRODUCTION":
            from app.services.production_cris import ProductionCrisGateway
            _gateway_instance = ProductionCrisGateway()
        else:
            from app.services.cris_simulator import CrisSimulatorGateway
            _gateway_instance = CrisSimulatorGateway()

    return _gateway_instance
