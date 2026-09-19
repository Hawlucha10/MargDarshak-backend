"""Station search and discovery endpoints."""

from typing import List
from fastapi import APIRouter, Query
from app.schemas.station import StationSearchResult

router = APIRouter()


@router.get("/stations/search", response_model=List[StationSearchResult])
async def search_stations(
    q: str = Query(..., min_length=1, description="Station name or code prefix (e.g. Gwal or GWL)"),
    limit: int = Query(10, ge=1, le=50),
):
    """Search stations by code or name prefix (autocomplete)."""
    # Placeholder implementation before database ingestion in Phase 1
    return [
        StationSearchResult(code="GWL", name="Gwalior Junction", zone="NCR", state="Madhya Pradesh"),
        StationSearchResult(code="PUNE", name="Pune Junction", zone="CR", state="Maharashtra"),
        StationSearchResult(code="BPL", name="Bhopal Junction", zone="WCR", state="Madhya Pradesh"),
        StationSearchResult(code="NGP", name="Nagpur Junction", zone="CR", state="Maharashtra"),
        StationSearchResult(code="NDLS", name="New Delhi", zone="NR", state="Delhi"),
    ]
