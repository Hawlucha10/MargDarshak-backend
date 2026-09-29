import json

with open("D:/Sih58/NishkarshFoundData/TAG_2026_complete_timetable.json", "r", encoding="utf-8") as f:
    trains = json.load(f)

stn_codes = {}
for t in trains:
    for s in t["stops"]:
        c = s["station_code"].upper().strip()
        name = s.get("station_name", "") or ""
        if c not in stn_codes:
            stn_codes[c] = {"count": 0, "name": name}
        stn_codes[c]["count"] += 1

print(f"Total distinct station codes in TAG JSON: {len(stn_codes)}")

# Check codes that end with M or J or weird suffix
anomalies = []
for c, d in stn_codes.items():
    if len(c) == 4 and (c.endswith("M") or c.endswith("J") or c.endswith("L") or c.endswith("A")):
        anomalies.append((c, d["name"], d["count"]))

print(f"\nPotential 4-letter truncated / suffixed codes: {len(anomalies)}")
for a in sorted(anomalies, key=lambda x: -x[2])[:30]:
    print(f"  Code: {a[0]:6s} | Name: {a[1]:25s} | Count: {a[2]}")
