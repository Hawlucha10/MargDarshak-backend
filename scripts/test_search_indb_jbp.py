import asyncio
from app.api.v1.search import search_routes
from app.schemas.route import RouteSearchRequest

async def test_search():
    req = RouteSearchRequest(
        origin="INDB",
        destination="JBP",
        travel_date="2026-09-22",
        max_transfers=2,
        priority="balanced"
    )
    res = await search_routes(req)
    print(f"Total routes found for INDB -> JBP: {res.total_routes_found}")
    for i, r in enumerate(res.routes):
        legs_desc = " + ".join(f"{l.train_number} {l.train_name} ({l.from_station}->{l.to_station} dep:{l.departure_time} arr:{l.arrival_time})" for l in r.legs)
        print(f"Route {i+1} [{r.label}] {r.total_travel_time} (Fare: Rs.{r.total_fare}, Transfers: {r.transfers}):")
        print(f"   {legs_desc}")

if __name__ == '__main__':
    asyncio.run(test_search())
