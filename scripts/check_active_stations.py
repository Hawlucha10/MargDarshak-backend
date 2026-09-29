import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text
from app.db.postgres import get_session_maker

async def check_active_stations():
    sm = get_session_maker()
    async with sm() as session:
        res = await session.execute(
            text("""
            SELECT count(DISTINCT station_code) 
            FROM timetable
            """)
        )
        timetable_stns = res.scalar()
        
        res2 = await session.execute(
            text("SELECT count(*) FROM stations")
        )
        total_stns = res2.scalar()
        
        # Check stations containing (NG) or (MG)
        res3 = await session.execute(
            text("SELECT code, name FROM stations WHERE name ILIKE '%(ng)%' OR name ILIKE '%(mg)%' OR name ILIKE '%narrow%'")
        )
        ng_stns = res3.fetchall()
        
        print(f"Total stations in DB: {total_stns}")
        print(f"Stations with active trains in timetable: {timetable_stns}")
        print(f"Obsolete NG / MG stations in DB: {len(ng_stns)}")
        for r in ng_stns[:10]:
            print(f"  {r[0]:6s} - {r[1]}")

asyncio.run(check_active_stations())
