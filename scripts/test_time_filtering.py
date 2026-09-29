import urllib.request
import json
import sys
from datetime import datetime, timezone, timedelta

sys.stdout.reconfigure(encoding="utf-8")
BASE_URL = "http://127.0.0.1:8000/api/v1"

IST = timezone(timedelta(hours=5, minutes=30))
now_ist = datetime.now(IST)
today_str = now_ist.strftime("%Y-%m-%d")
next_week_str = (now_ist + timedelta(days=7)).strftime("%Y-%m-%d")

print(f"Current IST Time: {now_ist.strftime('%Y-%m-%d %H:%M:%S')}")

def search(date_str):
    body = json.dumps({
        "origin": "NZM",
        "destination": "JBP",
        "travel_date": date_str,
        "priority": "balanced",
        "max_transfers": 2,
        "accessible_only": False,
    }).encode("utf-8")
    req = urllib.request.Request(f"{BASE_URL}/search", data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))

res_today = search(today_str)
print(f"\nResults for TODAY ({today_str}): Total routes = {res_today.get('total_routes_found')}")
for r in res_today.get("routes", []):
    f_leg = r["legs"][0]
    print(f"  Train {f_leg['train_number']}: Departs at {f_leg['departure_time']} from {f_leg['from_station']}")

res_future = search(next_week_str)
print(f"\nResults for FUTURE DATE ({next_week_str}): Total routes = {res_future.get('total_routes_found')}")
for r in res_future.get("routes", []):
    f_leg = r["legs"][0]
    print(f"  Train {f_leg['train_number']}: Departs at {f_leg['departure_time']} from {f_leg['from_station']}")
