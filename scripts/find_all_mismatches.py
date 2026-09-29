import json

with open("D:/Sih58/NishkarshFoundData/TAG_2026_complete_timetable.json", "r", encoding="utf-8") as f:
    trains = json.load(f)

with open("D:/Sih58/MargDarshak-backend/data/stations/stations_geo.geojson", "r", encoding="utf-8") as f:
    geo = json.load(f)

geo_by_code = {}
geo_by_name = {}
for feat in geo.get("features", []):
    props = feat.get("properties", {})
    c = props.get("code", "").strip().upper()
    n = props.get("name", "").strip().upper()
    if c:
        geo_by_code[c] = n
    if n:
        geo_by_name[n] = c

# Collect all codes from timetable
stn_map = {}
for t in trains:
    for s in t["stops"]:
        c = s["station_code"].upper().strip()
        name = (s.get("station_name") or "").strip()
        if c not in stn_map:
            stn_map[c] = set()
        if name:
            stn_map[c].add(name)

mismatches = []
for c, names in stn_map.items():
    name_sample = list(names)[0] if names else ""
    # Check if c is in geo_by_code
    if c not in geo_by_code:
        mismatches.append((c, name_sample, "NOT_IN_GEO"))
    else:
        # Check if name is vastly different
        geo_name = geo_by_code[c]
        # Compare
        n_clean = "".join(ch for ch in name_sample.upper() if ch.isalpha())
        g_clean = "".join(ch for ch in geo_name if ch.isalpha())
        if n_clean and g_clean and not any(part in g_clean for part in [n_clean[:4], g_clean[:4]]):
            mismatches.append((c, name_sample, f"NAME_MISMATCH vs {geo_name}"))

print(f"Total station codes in timetable: {len(stn_map)}")
print(f"Total potential mismatches: {len(mismatches)}")
for m in mismatches[:50]:
    print(f"  {m[0]:6s} | Name: {m[1]:25s} | Reason: {m[2]}")
