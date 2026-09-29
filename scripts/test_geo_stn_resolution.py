import json
import re
from pathlib import Path

# Load stations_geo
geo_path = Path("D:/Sih58/MargDarshak-backend/data/stations/stations_geo.geojson")
with open(geo_path, "r", encoding="utf-8") as f:
    geo_data = json.load(f)

geo_map = {}
for feat in geo_data.get("features", []):
    props = feat.get("properties", {})
    code = props.get("code", "").strip().upper()
    name = props.get("name", "").strip().upper()
    if code and name:
        geo_map[name] = code
        # clean variations: e.g. remove JN, CANTT, etc.
        norm_name = re.sub(r"\b(JN|JUNCTION|CANTT|TERMINUS|TER|RD|ROAD)\b", "", name).strip()
        norm_name = " ".join(norm_name.split())
        if norm_name and norm_name not in geo_map:
            geo_map[norm_name] = code

print(f"Loaded {len(geo_map)} station mappings from stations_geo.geojson")

# Test on the fallback names from the audit
test_names = ["PUNE", "RAIPUR", "KOTA", "SAWAI MADHOPUR", "LUCKNOW", "DURG", "GONDIA", "TATANAGAR", "KIUL", "BRAHMAPUR", "JABALPUR", "BHOPAL", "GWALIOR"]
for t in test_names:
    code = geo_map.get(t)
    if not code:
        # try partial
        matches = [f"{k} -> {v}" for k, v in geo_map.items() if t == k or t in k][:3]
        print(f"'{t}': {matches}")
    else:
        print(f"'{t}' -> {code}")
