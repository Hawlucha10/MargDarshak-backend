import asyncio
import sys
import time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text
from app.db.postgres import get_session_maker
from app.core.agrd import discover_stations_postgis
from app.core.raptor import RaptorRouter

async def test_raptor(orig, dest):
    sm = get_session_maker()
    async with sm() as session:
        stations = await discover_stations_postgis(session, orig, dest, focal_slack=1.35)
        codes = [s["code"] for s in stations]

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
        res = await session.execute(query_timetable, {"codes": codes})
        timetable_records = [dict(r._mapping) for r in res.fetchall()]

        t0 = time.time()
        router = RaptorRouter(timetable_records)
        t1 = time.time()
        journeys = router.plan(origin=orig, destination=dest, max_transfers=2, base_transfer_buffer_min=30)
        t2 = time.time()

        print(f"\n--- RAPTOR Results for {orig} -> {dest} ---")
        print(f"Router built in {(t1-t0)*1000:.1f}ms | Plan computed in {(t2-t1)*1000:.1f}ms")
        print(f"Total Journeys Found: {len(journeys)}")

        for idx, j in enumerate(journeys[:5]):
            print(f"\nOption {idx+1}: Transfers={j['transfers']}")
            for leg in j['legs']:
                print(f"  Train {leg['train_number']} ({leg['train_name']}): {leg['board_station']} ({leg['dep_time']}) -> {leg['alight_station']} ({leg['arr_time']})")

async def main():
    await test_raptor("NZM", "JBP")
    await test_raptor("NZM", "LAR") # Lalitpur check!
    await test_raptor("LAR", "JBP") # Transfer check!
    await test_raptor("GWL", "PUNE")

asyncio.run(main())
