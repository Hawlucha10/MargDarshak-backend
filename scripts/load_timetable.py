"""
Load timetable data from train_schedules.json into PostgreSQL.
"""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from app.db.postgres import get_engine, get_session_maker, Base
from app.db.models import StationModel, TimetableModel

DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "timetable" / "train_schedules.json"


def parse_time(time_str: str | None):
    """Safely parse time strings like '07:55:00' or 'None'."""
    if not time_str or time_str == "None" or time_str.strip() == "":
        return None
    try:
        return datetime.strptime(time_str.strip(), "%H:%M:%S").time()
    except ValueError:
        try:
            return datetime.strptime(time_str.strip(), "%H:%M").time()
        except ValueError:
            return None


async def load_timetable():
    print(f"Reading timetable from: {DATA_FILE}")
    if not DATA_FILE.exists():
        print(f"Error: File not found: {DATA_FILE}")
        return

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        schedules = json.load(f)

    print(f"Total schedule rows found: {len(schedules)}")

    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_maker = get_session_maker()

    # Pre-fetch existing station codes so we don't violate Foreign Keys
    async with session_maker() as session:
        result = await session.execute(select(StationModel.code))
        existing_stations = set(r[0] for r in result.fetchall())
        print(f"Known stations in database: {len(existing_stations)}")

    # Check for missing stations in schedule and add them as placeholders
    missing_stations = set()
    for row in schedules:
        st_code = row.get("station_code")
        if st_code:
            st_code = st_code.strip().upper()
            if st_code not in existing_stations:
                missing_stations.add((st_code, row.get("station_name", st_code).strip()))

    if missing_stations:
        print(f"Creating {len(missing_stations)} placeholder stations that were missing from geo data...")
        async with session_maker() as session:
            batch = [
                {
                    "code": code,
                    "name": name,
                    "lat": 0.0,
                    "lon": 0.0,
                }
                for code, name in missing_stations
            ]
            for i in range(0, len(batch), 1000):
                stmt = insert(StationModel).values(batch[i : i + 1000]).on_conflict_do_nothing()
                await session.execute(stmt)
            await session.commit()
            for code, _ in missing_stations:
                existing_stations.add(code)

    # Ingest timetable records in batches
    batch_size = 2000
    records = []
    inserted_count = 0

    async with session_maker() as session:
        for idx, row in enumerate(schedules):
            st_code = row.get("station_code")
            if not st_code:
                continue
            st_code = st_code.strip().upper()

            arrival = parse_time(row.get("arrival"))
            departure = parse_time(row.get("departure"))

            records.append({
                "train_number": str(row.get("train_number", "")).strip(),
                "train_name": str(row.get("train_name", "")).strip(),
                "station_code": st_code,
                "station_name": str(row.get("station_name", "")).strip(),
                "arrival": arrival,
                "departure": departure,
                "day": int(row.get("day", 1)),
                "stop_sequence": idx % 100,  # approximate sequence if not explicitly numbered
            })

            if len(records) >= batch_size:
                await session.execute(insert(TimetableModel).values(records))
                await session.commit()
                inserted_count += len(records)
                print(f"Ingested {inserted_count}/{len(schedules)} timetable records...")
                records = []

        if records:
            await session.execute(insert(TimetableModel).values(records))
            await session.commit()
            inserted_count += len(records)

    print(f"✅ Successfully ingested {inserted_count} timetable records into PostgreSQL!")


if __name__ == "__main__":
    asyncio.run(load_timetable())
