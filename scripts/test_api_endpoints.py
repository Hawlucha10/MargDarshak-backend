import urllib.request
import json
import time
import sys

sys.stdout.reconfigure(encoding="utf-8")

BASE_URL = "http://127.0.0.1:8000/api/v1"

def test_get(url):
    t0 = time.time()
    req = urllib.request.Request(url, headers={"User-Agent": "TestClient"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        elapsed = (time.time() - t0) * 1000
        return data, elapsed

def test_post(url, payload):
    t0 = time.time()
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json", "User-Agent": "TestClient"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        elapsed = (time.time() - t0) * 1000
        return data, elapsed

print("=== 1. Testing Station Search ===")
for q in ["LAR", "NZM", "JBP", "GWL", "PUNE"]:
    res, ms = test_get(f"{BASE_URL}/stations/search?q={q}&limit=3")
    print(f"Query '{q}' ({ms:.1f}ms): {[(r['code'], r['name']) for r in res]}")

print("\n=== 2. Testing Route Search: NZM -> JBP ===")
payload_nzm_jbp = {
    "origin": "NZM",
    "destination": "JBP",
    "travel_date": "2026-09-28",
    "priority": "balanced",
    "max_transfers": 2,
    "accessible_only": False,
}
res, ms = test_post(f"{BASE_URL}/search", payload_nzm_jbp)
print(f"NZM -> JBP completed in {ms:.1f}ms. Total routes found: {res.get('total_routes_found')}")
for idx, r in enumerate(res.get("routes", [])[:3]):
    legs_desc = " -> ".join(f"{leg['from_station']} ({leg['departure_time']}) to {leg['to_station']} ({leg['arrival_time']}) via {leg['train_number']}" for leg in r["legs"])
    print(f"  Route {idx+1} [{r['label']}]: Travel Time: {r['total_travel_time']}, Fare: ₹{r['total_fare']}, Transfers: {r['transfers']}")
    print(f"    Legs: {legs_desc}")

print("\n=== 3. Testing Route Search: LAR -> JBP (Intermediate Halt Search!) ===")
payload_lar_jbp = {
    "origin": "LAR",
    "destination": "JBP",
    "travel_date": "2026-09-28",
    "priority": "fastest",
    "max_transfers": 2,
    "accessible_only": False,
}
res, ms = test_post(f"{BASE_URL}/search", payload_lar_jbp)
print(f"LAR -> JBP completed in {ms:.1f}ms. Total routes found: {res.get('total_routes_found')}")
for idx, r in enumerate(res.get("routes", [])[:2]):
    legs_desc = " -> ".join(f"{leg['from_station']} ({leg['departure_time']}) to {leg['to_station']} ({leg['arrival_time']}) via {leg['train_number']}" for leg in r["legs"])
    print(f"  Route {idx+1} [{r['label']}]: Travel Time: {r['total_travel_time']}, Fare: ₹{r['total_fare']}, Transfers: {r['transfers']}")
    print(f"    Legs: {legs_desc}")

print("\n=== 4. Testing Route Search: GWL -> PUNE ===")
payload_gwl_pune = {
    "origin": "GWL",
    "destination": "PUNE",
    "travel_date": "2026-09-28",
    "priority": "balanced",
    "max_transfers": 2,
    "accessible_only": False,
}
res, ms = test_post(f"{BASE_URL}/search", payload_gwl_pune)
print(f"GWL -> PUNE completed in {ms:.1f}ms. Total routes found: {res.get('total_routes_found')}")
for idx, r in enumerate(res.get("routes", [])[:2]):
    legs_desc = " -> ".join(f"{leg['from_station']} ({leg['departure_time']}) to {leg['to_station']} ({leg['arrival_time']}) via {leg['train_number']}" for leg in r["legs"])
    print(f"  Route {idx+1} [{r['label']}]: Travel Time: {r['total_travel_time']}, Fare: ₹{r['total_fare']}, Transfers: {r['transfers']}")
    print(f"    Legs: {legs_desc}")
