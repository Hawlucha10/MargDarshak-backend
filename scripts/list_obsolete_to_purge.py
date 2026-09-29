import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text
from app.db.postgres import get_session_maker

async def clean_deprecated():
    sm = get_session_maker()
    async with sm() as session:
        # Check all stations with (ng), (mg)
        res = await session.execute(
            text("SELECT code, name FROM stations WHERE name ILIKE '%(ng)%' OR name ILIKE '%(mg)%' OR name ILIKE '%narrow gauge%' OR name ILIKE '%meter gauge%'")
        )
        rows = res.fetchall()
        print("Obsolete NG / MG stations to purge:")
        for r in rows:
            print(f"  DELETE {r[0]:6s} - {r[1]}")

asyncio.run(clean_deprecated())
