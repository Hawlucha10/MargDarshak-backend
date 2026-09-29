import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text
from app.db.postgres import get_session_maker

async def check_22191():
    sm = get_session_maker()
    async with sm() as session:
        res = await session.execute(
            text("SELECT stop_sequence, station_code, station_name, arrival, departure, day FROM timetable WHERE train_number = '22191' ORDER BY stop_sequence")
        )
        rows = res.fetchall()
        print(f"Train 22191 in PostgreSQL: {len(rows)} stops")
        for r in rows:
            print(f"  Seq {r[0]:2d}: {r[1]:6s} - {r[2]:25s} Arr: {r[3]} Dep: {r[4]} Day: {r[5]}")

asyncio.run(check_22191())
