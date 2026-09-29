import json

with open("D:/Sih58/NishkarshFoundData/TAG_2026_complete_timetable.json", "r", encoding="utf-8") as f:
    trains = json.load(f)

geo_path = "D:/Sih58/MargDarshak-backend/data/stations/stations_geo.geojson"
with open(geo_path, "r", encoding="utf-8") as f:
    geo = json.load(f)

geo_codes = set()
for feat in geo.get("features", []):
    c = feat.get("properties", {}).get("code", "").strip().upper()
    if c:
        geo_codes.add(c)

# also add modern known
known = {"DDU", "VGLJ", "PRYJ", "BSBS", "RKMP", "SMVB", "AYC", "AY", "MCSC"}
geo_codes.update(known)

unmapped = {}
for t in trains:
    for s in t["stops"]:
        c = s["station_code"].upper()
        if c not in geo_codes:
            if c not in unmapped:
                unmapped[c] = {"count": 0, "names": set()}
            unmapped[c]["count"] += 1
            if s.get("station_name"):
                unmapped[c]["names"].add(s["station_name"])

print(f"Total unmapped codes: {len(unmapped)}")
for c, data in sorted(unmapped.items(), key=lambda x: -x[1]["count"]):
    names = list(data["names"])[:2]
    print(f"{c:6s}: count={data['count']:3d} | names={names}")
