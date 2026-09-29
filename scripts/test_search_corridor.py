import asyncio
import sys
import time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text
from app.db.postgres import get_session_maker
from app.core.agrd import discover_stations_postgis

async def test_corridor_query(orig, dest):
    sm = get_session_maker()
    async with sm() as session:
        t0 = time.time()
        stations = await discover_stations_postgis(session, orig, dest, focal_slack=1.35)
        codes = [s["code"] for s in stations]
        t1 = time.time()
        print(f"\nDiscovered {len(codes)} stations for {orig} -> {dest} in {(t1-t0)*1000:.1f}ms")

        query_timetable = text(
            """
            WITH relevant_trains AS (
                SELECT DISTINCT train_number
                FROM timetable
                WHERE station_code = ANY(:codes)
            )
            SELECT t.train_number, t.train_name, t.station_code, t.station_name, 
                   to_char(t.arrival, 'HH24:MI:SS') as arrival,
                   to_char(t.departure, 'HH24:MI:SS') as departure,
                   t.day, t.stop_sequence
            FROM timetable t
            JOIN relevant_trains rt ON t.train_number = rt.train_number
            WHERE t.station_code = ANY(:codes)
            ORDER BY t.train_number, t.day, t.stop_sequence
            """
        )
        t2 = time.time()
        res = await session.execute(query_timetable, {"codes": codes})
        rows = res.fetchall()
        t3 = time.time()
        print(f"Retrieved {len(rows)} timetable records across relevant corridor trains in {(t3-t2)*1000:.1f}ms")

        # Check if 22182 is in the records
        train_nums = set(r[0] for r in rows)
        print(f"Total distinct trains running in this corridor: {len(train_nums)}")
        if "22182" in train_nums:
            print(">>> Train 22182 is PRESENT in corridor timetable!")

async def main():
    await test_corridor_query("NZM", "JBP")
    await test_corridor_query("GWL", "PUNE")

asyncio.run(main())
