"""
MargDarshak — AI-Augmented Intercity Railway Route Planner
FastAPI Application Entry Point

SIH 2025 | PS: T02 | Team: Binary Beacons
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.api.v1 import availability, search, stations, trains, chat


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup & shutdown events — connect/disconnect databases."""
    # --- STARTUP ---
    settings = get_settings()
    print(f"[STARTUP] MargDarshak API starting on {settings.api_host}:{settings.api_port}")
    print(f"[STARTUP] PostgreSQL: {settings.postgres_host}:{settings.postgres_port}/{settings.postgres_db}")
    print(f"[STARTUP] Redis: {settings.redis_host}:{settings.redis_port}")
    try:
        from app.ml.delay_predictor import get_predictor
        get_predictor()
        print("[STARTUP] Pre-warmed ML Delay Predictor Ensemble successfully")
    except Exception as e:
        print(f"[STARTUP] ML pre-warming warning: {e}")

    yield  # App is running

    # --- SHUTDOWN ---
    print("[SHUTDOWN] MargDarshak API shutting down...")
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

# CORS — allow frontend to call this API (support localhost, 127.0.0.1 on any port)
settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ],
    allow_origin_regex=r"https?://.*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routes
app.include_router(search.router, prefix="/api/v1", tags=["Search"])
app.include_router(stations.router, prefix="/api/v1", tags=["Stations"])
app.include_router(trains.router, prefix="/api/v1", tags=["Trains"])
app.include_router(availability.router, prefix="/api/v1", tags=["Availability"])
app.include_router(chat.router, prefix="/api/v1", tags=["Chat"])


@app.get("/", tags=["Health"])
async def root():
    """Root endpoint — confirms API is running."""
    return {"service": "MargDarshak", "status": "running", "version": "0.1.0"}


@app.get("/health", tags=["Health"])
@app.get("/api/v1/health", tags=["Health"])
async def health_check():
    """Health check — reports real-time status of all connected services."""
    db_status = "unavailable"
    try:
        from app.db.postgres import get_session_maker
        from sqlalchemy import text
        session_maker = get_session_maker()
        async with session_maker() as session:
            await session.execute(text("SELECT 1"))
            db_status = "connected"
    except Exception:
        db_status = "error"

    redis_status = "unavailable"
    try:
        from app.db.redis_client import get_redis
        redis = get_redis()
        pong = await redis.ping()
        if pong:
            redis_status = "connected"
    except Exception:
        redis_status = "error"

    ml_status = "unavailable"
    try:
        from app.ml.delay_predictor import get_predictor
        p = get_predictor()
        if p.ready:
            ml_status = "ready"
    except Exception:
        ml_status = "error"

    return {
        "status": "ok",
        "services": {
            "api": "running",
            "database": db_status,
            "redis": redis_status,
            "ml_model": ml_status,
        },
    }
