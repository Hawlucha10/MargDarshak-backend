"""
Load station geospatial data from stations_geo.geojson into PostgreSQL/PostGIS.
"""

import asyncio
import json
import os
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from app.db.postgres import get_engine, get_session_maker, Base
from app.db.models import StationModel

DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "stations" / "stations_geo.geojson"


async def load_stations():
    print(f"Reading station data from: {DATA_FILE}")
    if not DATA_FILE.exists():
        print(f"Error: File not found: {DATA_FILE}")
        return

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        geojson = json.load(f)

    features = geojson.get("features", [])
    print(f"Total station features found: {len(features)}")

    engine = get_engine()
    async with engine.begin() as conn:
        # Create tables if they do not exist
        await conn.run_sync(Base.metadata.create_all)

    session_maker = get_session_maker()
    batch_size = 500
    records = []
    inserted_count = 0

    async with session_maker() as session:
        for feature in features:
            props = feature.get("properties", {})
            geom = feature.get("geometry", {})
            coords = geom.get("coordinates", [0, 0])

            code = props.get("code")
            name = props.get("name")
            if not code or not name:
                continue

            lon, lat = coords[0], coords[1]
            state = props.get("state")
            zone = props.get("zone")
            address = props.get("address")

            # PostGIS Point string: SRID=4326;POINT(lon lat)
            point_wkt = f"SRID=4326;POINT({lon} {lat})"

            record = {
                "code": code.strip().upper(),
                "name": name.strip(),
                "state": state.strip() if state else None,
                "zone": zone.strip().upper() if zone else None,
                "address": address.strip() if address else None,
                "lat": lat,
                "lon": lon,
                "geom": point_wkt,
            }
            records.append(record)

            if len(records) >= batch_size:
                stmt = insert(StationModel).values(records)
                stmt = stmt.on_conflict_do_update(
                    index_elements=[StationModel.code],
                    set_={
                        "name": stmt.excluded.name,
                        "lat": stmt.excluded.lat,
                        "lon": stmt.excluded.lon,
                        "geom": stmt.excluded.geom,
                        "zone": stmt.excluded.zone,
                        "state": stmt.excluded.state,
                    },
                )
                await session.execute(stmt)
                await session.commit()
                inserted_count += len(records)
                print(f"Processed {inserted_count}/{len(features)} stations...")
                records = []

        if records:
            stmt = insert(StationModel).values(records)
            stmt = stmt.on_conflict_do_update(
                index_elements=[StationModel.code],
                set_={
                    "name": stmt.excluded.name,
                    "lat": stmt.excluded.lat,
                    "lon": stmt.excluded.lon,
                    "geom": stmt.excluded.geom,
                    "zone": stmt.excluded.zone,
                    "state": stmt.excluded.state,
                },
            )
            await session.execute(stmt)
            await session.commit()
            inserted_count += len(records)

    print(f"[SUCCESS] Ingested {inserted_count} stations into PostGIS!")


if __name__ == "__main__":
    asyncio.run(load_stations())
