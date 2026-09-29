import asyncio
from sqlalchemy import text
from app.db.postgres import get_session_maker

# List of suspicious codes to inspect all variations of their tt_stn_name
SUSPICIOUS = [
    'MANG', 'BLLI', 'NED', 'TK', 'MYS', 'ALLP', 'SGO', 'RDM', 'BGM', 'NGE',
    'BYL', 'BETI', 'ADT', 'NGN', 'APTA', 'USL', 'KEA', 'SMVB', 'WADI', 'CAPE',
    'PG', 'KURN', 'AGC', 'ANR', 'GMO', 'UMD', 'VEER', 'HPT', 'BJP', 'HPU',
    'THAN', 'BJU', 'KGA', 'ADX', 'SHIV', 'HATI', 'BLRD', 'MKHI', 'HAPA', 'RAYA', 'INDM'
]

async def inspect():
    sm = get_session_maker()
    async with sm() as db:
        res = await db.execute(text("""
            SELECT station_code, station_name, count(*) as cnt
            FROM timetable
            WHERE station_code = ANY(:codes)
            GROUP BY station_code, station_name
            ORDER BY station_code, cnt DESC
        """), {"codes": SUSPICIOUS})
        
        for r in res.fetchall():
            print(f"{r.station_code:6s} | {r.station_name:40s} | {r.cnt} stops")

if __name__ == '__main__':
    asyncio.run(inspect())
