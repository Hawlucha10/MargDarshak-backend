import urllib.request
import json
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

try:
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        print(f"SUCCESS: Status 200 OK! Total routes found: {data.get('total_routes_found')}")
        for idx, r in enumerate(data.get("routes", [])):
            print(f"  Route {idx+1} [{r['label']}]: Time={r['total_travel_time']}, Fare=Rs.{r['total_fare']}, Transfers={r['transfers']}")
            for leg in r["legs"]:
                print(f"    Leg: Train {leg['train_number']} {leg['train_name']}: {leg['from_station']} ({leg['departure_time']}) -> {leg['to_station']} ({leg['arrival_time']})")
except urllib.error.HTTPError as e:
    print(f"HTTP Error {e.code}: {e.read().decode('utf-8')}")
except Exception as e:
    print("Error:", type(e), e)
