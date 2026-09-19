"""
Master seed script to populate PostgreSQL/PostGIS with stations, timetables, and delay data.
"""

import asyncio
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.load_stations import load_stations
from scripts.load_timetable import load_timetable
from scripts.load_delay_data import load_delay_data


async def main():
    start_total = time.time()
    print("==================================================")
    print("🚆 MargDarshak Database Seeding Pipeline")
    print("==================================================")

    print("\n--- STEP 1: Ingesting Station Geospatial Data ---")
    t1 = time.time()
    await load_stations()
    print(f"Step 1 completed in {round(time.time() - t1, 2)}s")

    print("\n--- STEP 2: Ingesting Timetable Schedules ---")
    t2 = time.time()
    await load_timetable()
    print(f"Step 2 completed in {round(time.time() - t2, 2)}s")

    print("\n--- STEP 3: Ingesting Delay Training Data (100k sample) ---")
    t3 = time.time()
    await load_delay_data(sample_limit=100000)
    print(f"Step 3 completed in {round(time.time() - t3, 2)}s")

    total_time = round(time.time() - start_total, 2)
    print("\n==================================================")
    print(f"🎉 Database Seeding Complete in {total_time}s!")
    print("==================================================")


if __name__ == "__main__":
    asyncio.run(main())
