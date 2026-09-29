import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select
from app.db.postgres import get_session_maker
from app.db.models import StationModel

async def check_stations():
    sm = get_session_maker()
    async with sm() as session:
        res = await session.execute(
            select(StationModel).where(StationModel.code.ilike("%JBP%") | StationModel.name.ilike("%Jabalpur%"))
        )
        rows = res.scalars().all()
        print(f"Stations matching JBP / Jabalpur in DB: {len(rows)}")
        for r in rows:
            print(f"  Code: {r.code:8s} | Name: {r.name:30s} | State: {r.state} | Zone: {r.zone}")

asyncio.run(check_stations())
