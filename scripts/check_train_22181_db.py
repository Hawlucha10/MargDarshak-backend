import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text
from app.db.postgres import get_session_maker

async def check_train_in_db():
    sm = get_session_maker()
    async with sm() as session:
        res = await session.execute(
            text("SELECT train_number, station_code, station_name, arrival, departure, stop_sequence, day FROM timetable WHERE train_number = '22181' ORDER BY stop_sequence")
        )
        rows = res.fetchall()
        print(f"Train 22181 in PostgreSQL timetable: {len(rows)} stops found")
        for r in rows:
            print(f"  Stop {r[5]:2d} (Day {r[6]}): {r[1]:<6} {r[2]:<30} Arr: {r[3]} Dep: {r[4]}")

asyncio.run(check_train_in_db())
