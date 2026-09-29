import asyncio
from sqlalchemy import text
from app.db.postgres import get_session_maker

TARGET_CODES = [
    'MAJN', 'MAQ', 'UBL', 'MV', 'NDPM', 'SEGM', 'PRYJ', 'PCOI', 'NKB', 'BSBS',
    'MCTM', 'BTH', 'UMB', 'MBDP', 'VSKP', 'GHY', 'KCVL', 'TVC', 'CPK', 'INDB',
    'SVDK', 'SKZR', 'KRNT', 'SIOB', 'RJN', 'KPG', 'SMVB', 'SMET', 'PTKC', 'SMVJ',
    'KWV', 'BAND', 'AWB', 'ANG', 'SUNR', 'SGNR', 'SNSI', 'MBNR', 'VZM', 'SHRN',
    'GTNR', 'RJPB', 'VPT', 'TATA', 'YNRK', 'EKNR', 'KRMR', 'SKTN', 'SINA', 'DADN',
    'ROJ', 'HMT'
]

async def check_existence():
    sm = get_session_maker()
    async with sm() as db:
        res = await db.execute(text("SELECT code FROM stations WHERE code = ANY(:codes)"), {"codes": TARGET_CODES})
        existing = {r.code for r in res.fetchall()}
        missing = [c for c in TARGET_CODES if c not in existing]
        print(f"Total target codes: {len(TARGET_CODES)}")
        print(f"Existing in stations table: {len(existing)}")
        print(f"Missing in stations table: {missing}")

if __name__ == '__main__':
    asyncio.run(check_existence())
