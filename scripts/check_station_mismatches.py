import asyncio
from sqlalchemy import text
from app.db.postgres import get_session_maker

async def check_mismatches():
    sm = get_session_maker()
    async with sm() as db:
        res = await db.execute(text("""
            SELECT t.station_code, s.name as db_stn_name, t.station_name as tt_stn_name, count(*) as cnt
            FROM timetable t
            JOIN stations s ON t.station_code = s.code
            WHERE lower(s.name) NOT LIKE '%' || lower(substr(trim(t.station_name), 1, 4)) || '%'
              AND length(trim(t.station_name)) > 4
            GROUP BY t.station_code, s.name, t.station_name
            HAVING count(*) >= 2
            ORDER BY cnt DESC
            LIMIT 50
        """))
        for r in res.fetchall():
            print(f"{r.station_code:6s} (DB: {r.db_stn_name:25s}) vs TT: '{r.tt_stn_name}' ({r.cnt} stops)")

if __name__ == '__main__':
    asyncio.run(check_mismatches())
