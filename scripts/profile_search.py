import asyncio
import sys
import time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.schemas.route import RouteSearchRequest
from app.api.v1.search import search_routes

async def profile():
    req = RouteSearchRequest(
        origin="GWL",
        destination="JBP",
        travel_date="2026-09-28",
        priority="balanced",
        max_transfers=2,
        accessible_only=False,
    )
    t0 = time.time()
    res = await search_routes(req)
    t1 = time.time()
    print(f"search_routes completed in {(t1-t0)*1000:.1f}ms")
    print(f"Total routes found: {res.total_routes_found}")

asyncio.run(profile())
