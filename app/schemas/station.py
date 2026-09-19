"""Station data schemas."""

from typing import Optional
from pydantic import BaseModel, Field


class StationBase(BaseModel):
    code: str = Field(..., description="IRCTC station code, e.g., GWL, BPL", max_length=10)
    name: str = Field(..., description="Full station name")
    state: Optional[str] = Field(None, description="State in India")
    zone: Optional[str] = Field(None, description="Railway Zone (e.g., NCR, CR, WR)")
    address: Optional[str] = Field(None, description="Detailed address/location")
    lat: float = Field(..., description="Latitude coordinate")
    lon: float = Field(..., description="Longitude coordinate")


class StationResponse(StationBase):
    pass


class StationSearchResult(BaseModel):
    code: str
    name: str
    zone: Optional[str] = None
    state: Optional[str] = None
