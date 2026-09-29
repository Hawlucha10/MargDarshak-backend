import asyncio
from app.services.station_service import search_stations

async def test():
    for q in ['jbp', 'indore', 'delhi', 'jabalpur', 'prayagraj', 'gwl', 'pune', 'shirdi', 'katra']:
        res = await search_stations(q)
        print(f"=== Query: '{q}' ({len(res)} results) ===")
        for r in res[:5]:
            print(f"  {r.code:6s} | {r.name:30s} | {r.state:15s} | Hub: {r.is_hub}")

if __name__ == '__main__':
    asyncio.run(test())
