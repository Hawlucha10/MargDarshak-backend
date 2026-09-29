import json
from collections import Counter

with open("D:/Sih58/NishkarshFoundData/TAG_2026_complete_timetable.json", "r", encoding="utf-8") as f:
    trains = json.load(f)

# Find all distinct station names and their current codes
name_to_codes = {}
for t in trains:
    for s in t["stops"]:
        name = (s.get("station_name") or "").strip()
        code = s.get("station_code", "").strip().upper()
        if not name:
            continue
        if name not in name_to_codes:
            name_to_codes[name] = Counter()
        name_to_codes[name][code] += 1

print(f"Total distinct station names: {len(name_to_codes)}")

# Let's inspect names that have multiple codes or wrong code
issues = []
for name, codes in name_to_codes.items():
    if len(codes) > 1:
        issues.append((name, dict(codes)))

print(f"Station names with multiple assigned codes: {len(issues)}")
for name, codes in sorted(issues, key=lambda x: -sum(x[1].values()))[:40]:
    print(f"  {name:30s} -> {codes}")
