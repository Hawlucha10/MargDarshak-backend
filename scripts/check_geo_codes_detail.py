import json

with open("D:/Sih58/MargDarshak-backend/data/stations/stations_geo.geojson", "r", encoding="utf-8") as f:
    geo = json.load(f)

check_codes = ["INDM", "INDB", "ADIJ", "ADI", "CPNL", "CNB", "RTLM", "RTM", "MALA", "RKMP", "RAYA", "SMVB", "BELA", "BGM", "ADRA", "BHC", "HAPA", "VSKP"]

for feat in geo.get("features", []):
    c = feat.get("properties", {}).get("code", "").strip().upper()
    if c in check_codes:
        print(f"GeoJSON: Code={c:<6} Name={feat.get('properties', {}).get('name')}")
