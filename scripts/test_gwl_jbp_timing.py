import urllib.request
import json
import time
import sys

sys.stdout.reconfigure(encoding="utf-8")
url = "http://127.0.0.1:8000/api/v1/search"
payload = {
    "origin": "GWL",
    "destination": "JBP",
    "travel_date": "2026-09-28",
    "priority": "balanced",
    "max_transfers": 2,
    "accessible_only": False,
}

body = json.dumps(payload).encode("utf-8")
req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})

t0 = time.time()
try:
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        elapsed = time.time() - t0
        print(f"Status 200 OK in {elapsed:.2f}s! Total routes: {data.get('total_routes_found')}")
        for r in data.get("routes", []):
            legs_str = " -> ".join(f"{l['from_station']} ({l['departure_time']}) to {l['to_station']} ({l['arrival_time']}) via {l['train_number']}" for l in r["legs"])
            print(f"  [{r['label']}] Time: {r['total_travel_time']}, Fare: Rs.{r['total_fare']}, Transfers: {r['transfers']}")
            print(f"    {legs_str}")
except Exception as e:
    print(f"Error after {time.time()-t0:.2f}s:", type(e), e)
