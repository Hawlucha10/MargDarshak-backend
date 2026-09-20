"""
Load historical delay training records from ir_train.csv into PostgreSQL.
"""

import asyncio
import sys
from datetime import datetime
from pathlib import Path
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy.dialects.postgresql import insert
from app.db.postgres import get_engine, get_session_maker, Base
from app.db.models import DelayRecordModel

DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "delay_prediction" / "ir_train.csv"


async def load_delay_data(sample_limit: int | None = 100000):
    print(f"Reading delay records from: {DATA_FILE}")
    if not DATA_FILE.exists():
        print(f"Error: File not found: {DATA_FILE}")
        return

    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_maker = get_session_maker()

    # Read CSV in chunks using pandas
    chunksize = 5000
    total_loaded = 0

    print(f"Processing CSV in chunks of {chunksize} (limit: {sample_limit or 'ALL'})...")

    async with session_maker() as session:
        for chunk in pd.read_csv(DATA_FILE, chunksize=chunksize, low_memory=False):
            records = []
            for _, row in chunk.iterrows():
                dep_date = None
                if pd.notna(row.get("departure_date")):
                    try:
                        dep_date = datetime.strptime(str(row["departure_date"]), "%Y-%m-%d").date()
                    except ValueError:
                        pass

                records.append({
                    "journey_id": str(row.get("journey_id", ""))[:30],
                    "train_number": str(row.get("train_number", ""))[:10],
                    "train_type": str(row.get("train_type", ""))[:50],
                    "departure_date": dep_date,
                    "month": int(row["month"]) if pd.notna(row.get("month")) else None,
                    "day_of_week": int(row["day_of_week"]) if pd.notna(row.get("day_of_week")) else None,
                    "zone": str(row.get("zone_abbr", row.get("zone", "")))[:20],
                    "distance_km": int(row["distance_km"]) if pd.notna(row.get("distance_km")) else None,
                    "is_fog_risk": bool(row.get("is_fog_risk", 0)),
                    "is_monsoon_season": bool(row.get("is_monsoon_season", 0)),
                    "fog_risk_score": float(row["fog_risk_score"]) if pd.notna(row.get("fog_risk_score")) else None,
                    "zone_congestion_index": float(row["zone_congestion_index"]) if pd.notna(row.get("zone_congestion_index")) else None,
                    "delay_minutes": int(row["delay_minutes"]) if pd.notna(row.get("delay_minutes")) else 0,
                    "is_delayed": bool(row.get("is_delayed", 0)),
                })

            if records:
                # asyncpg limit is 32767 parameters. 1000 rows * 14 columns = 14000 params (safe)
                sub_batch_size = 1000
                for i in range(0, len(records), sub_batch_size):
                    sub = records[i : i + sub_batch_size]
                    await session.execute(insert(DelayRecordModel).values(sub))
                await session.commit()
                total_loaded += len(records)
                print(f"Ingested {total_loaded} delay records...")

            if sample_limit and total_loaded >= sample_limit:
                print(f"Reached sample limit of {sample_limit} records.")
                break

    print(f"[SUCCESS] Ingested {total_loaded} delay records into PostgreSQL!")


if __name__ == "__main__":
    asyncio.run(load_delay_data())
