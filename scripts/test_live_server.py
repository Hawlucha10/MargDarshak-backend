import urllib.request
import json

print("=== 1. Test JBP station search ===")
with urllib.request.urlopen("http://127.0.0.1:8000/api/v1/stations/search?q=jbp") as resp:
    data = json.loads(resp.read().decode("utf-8"))
    print(f"JBP search results count: {len(data)}")
    for s in data:
        print(f"  {s['code']:6s} | {s['name']}")

print("\n=== 2. Test INDORE station search ===")
with urllib.request.urlopen("http://127.0.0.1:8000/api/v1/stations/search?q=indore") as resp:
    data = json.loads(resp.read().decode("utf-8"))
    print(f"INDORE search results count: {len(data)}")
    for s in data:
        print(f"  {s['code']:6s} | {s['name']}")

print("\n=== 3. Test INDB -> JBP route search ===")
req = urllib.request.Request(
    "http://127.0.0.1:8000/api/v1/search",
    data=json.dumps({"origin": "INDB", "destination": "JBP", "travel_date": "2026-09-22"}).encode("utf-8"),
    headers={"Content-Type": "application/json"}
)
with urllib.request.urlopen(req) as resp:
    data = json.loads(resp.read().decode("utf-8"))
    print(f"INDB -> JBP total routes found: {data.get('total_routes_found')}")
    for r in data.get("routes", []):
        legs = " + ".join(f"{l['train_number']} {l['train_name']} ({l['from_station']} {l['departure_time']} -> {l['to_station']} {l['arrival_time']})" for l in r.get("legs", []))
        print(f"  [{r.get('label'):13s}] ({r.get('total_travel_time')}, transfers={r.get('transfers')}, fare=Rs.{r.get('total_fare')}): {legs}")

print("\n=== 4. Test NDLS -> PRYJ route search ===")
req2 = urllib.request.Request(
    "http://127.0.0.1:8000/api/v1/search",
    data=json.dumps({"origin": "NDLS", "destination": "PRYJ", "travel_date": "2026-09-22"}).encode("utf-8"),
    headers={"Content-Type": "application/json"}
)
with urllib.request.urlopen(req2) as resp:
    data2 = json.loads(resp.read().decode("utf-8"))
    print(f"NDLS -> PRYJ total routes found: {data2.get('total_routes_found')}")
    for r in data2.get("routes", [])[:5]:
        legs = " + ".join(f"{l['train_number']} {l['train_name']} ({l['from_station']} {l['departure_time']} -> {l['to_station']} {l['arrival_time']})" for l in r.get("legs", []))
        print(f"  [{r.get('label'):13s}] ({r.get('total_travel_time')}, transfers={r.get('transfers')}, fare=Rs.{r.get('total_fare')}): {legs}")
