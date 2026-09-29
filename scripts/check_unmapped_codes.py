import json
from pathlib import Path

geo_path = Path("D:/Sih58/MargDarshak-backend/data/stations/stations_geo.geojson")
with open(geo_path, "r", encoding="utf-8") as f:
    geo = json.load(f)

geo_codes = set()
for feat in geo.get("features", []):
    c = feat.get("properties", {}).get("code", "").strip().upper()
    if c:
        geo_codes.add(c)

with open("D:/Sih58/NishkarshFoundData/TAG_2026_complete_timetable.json", "r", encoding="utf-8") as f:
    trains = json.load(f)

missing = {}
for t in trains:
    for s in t["stops"]:
        c = s["station_code"].upper()
        if c not in geo_codes:
            missing[c] = missing.get(c, 0) + 1

print(f"Total distinct codes in timetable not in geo_codes: {len(missing)}")
for c, cnt in sorted(missing.items(), key=lambda x: -x[1])[:30]:
    print(f"  {c}: {cnt} stops")
