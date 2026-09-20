"""Station search and discovery endpoints."""

from typing import List, Optional
from fastapi import APIRouter, Query
from app.schemas.station import StationSearchResult
from app.services.station_service import (
    search_stations as search_stations_service,
    get_popular_stations as get_popular_stations_service,
)

router = APIRouter()


@router.get("/stations/search", response_model=List[StationSearchResult])
async def search_stations(
    q: Optional[str] = Query(None, description="Station name, code, or city (e.g. GWL, Gwalior, NDLS, Delhi, Noida)"),
    limit: int = Query(15, ge=1, le=50),
):
    """
    Real-time autocomplete search across all 8,989 Indian Railway stations.
    Supports station code prefix/exact, station name, city hubs, and satellite nearby stations.
    """
    if not q or not q.strip():
        return get_popular_stations_service()[:limit]
    return await search_stations_service(query=q, limit=limit)


@router.get("/stations/popular", response_model=List[StationSearchResult])
async def get_popular_stations(limit: int = Query(10, ge=1, le=20)):
    """Return top major railway hub terminals (e.g., NDLS, GWL, PUNE, CSTM, HWH, SBC)."""
    return get_popular_stations_service()[:limit]
