"""
MargDarshak — AI-Augmented Intercity Railway Route Planner
FastAPI Application Entry Point

SIH 2025 | PS: T02 | Team: Binary Beacons
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.api.v1 import search, stations, trains


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup & shutdown events — connect/disconnect databases."""
    # --- STARTUP ---
    settings = get_settings()
    print(f"🚆 MargDarshak API starting on {settings.api_host}:{settings.api_port}")
    print(f"📦 PostgreSQL: {settings.postgres_host}:{settings.postgres_port}/{settings.postgres_db}")
    print(f"⚡ Redis: {settings.redis_host}:{settings.redis_port}")

    # Database connections will be initialized here in Phase 1
    # await db.connect()
    # await redis.connect()

    yield  # App is running

    # --- SHUTDOWN ---
    print("🛑 MargDarshak API shutting down...")
    # await db.disconnect()
    # await redis.disconnect()


# Create FastAPI app
app = FastAPI(
    title="MargDarshak API",
    description=(
        "AI-Augmented Intercity Railway Route Planner — "
        "discovers optimal multi-hop train connections with "
        "delay-aware scheduling, fare arbitrage & Pareto-optimal ranking."
    ),
    version="0.1.0",
    lifespan=lifespan,
)

# CORS — allow frontend to call this API
settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routes
app.include_router(search.router, prefix="/api/v1", tags=["Search"])
app.include_router(stations.router, prefix="/api/v1", tags=["Stations"])
app.include_router(trains.router, prefix="/api/v1", tags=["Trains"])


@app.get("/", tags=["Health"])
async def root():
    """Root endpoint — confirms API is running."""
    return {"service": "MargDarshak", "status": "running", "version": "0.1.0"}


@app.get("/api/v1/health", tags=["Health"])
async def health_check():
    """Health check — reports status of all connected services."""
    return {
        "status": "ok",
        "services": {
            "api": "running",
            "database": "pending",  # Will be "connected" after Phase 1
            "redis": "pending",
            "ml_model": "pending",
        },
    }
