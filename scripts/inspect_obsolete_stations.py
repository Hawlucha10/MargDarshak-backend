import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select, text
from app.db.postgres import get_session_maker
from app.db.models import StationModel

async def inspect_obsolete():
    sm = get_session_maker()
    async with sm() as session:
        res = await session.execute(
            text("""
            SELECT code, name, state, zone 
            FROM stations 
            WHERE name ILIKE '%(ng)%' 
               OR name ILIKE '%(mg)%' 
               OR name ILIKE '%(narrow)%'
               OR name ILIKE '%(meter)%'
               OR code LIKE '%N' AND length(code) = 4 AND name ILIKE '%jn%'
            """)
        )
        rows = res.fetchall()
        print(f"Total obsolete/NG stations: {len(rows)}")
        for r in rows:
            print(f"  {r[0]:6s} : {r[1]}")

asyncio.run(inspect_obsolete())
