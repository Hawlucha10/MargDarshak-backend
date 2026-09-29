import urllib.request
import json
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

# Test confirmtkt public schedule api
url = "https://ctapi.confirmtkt.com/api/trains/schedule?trainNo=22182"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

try:
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=10, context=ctx) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        print(f"ConfirmTkt API Success! Keys: {data.keys()}")
        schedule = data.get("schedule", []) or data.get("data", {}).get("schedule", [])
        print(f"Stops returned: {len(schedule)}")
        for s in schedule[:15]:
            print(f"  {s.get('stationCode')} {s.get('stationName')} Arr: {s.get('arrivalTime')} Dep: {s.get('departureTime')}")
except Exception as e:
    print(f"ConfirmTkt API Error: {e}")
