import json
from pathlib import Path

geo_path = Path("D:/Sih58/MargDarshak-backend/data/stations/stations_geo.geojson")
with open(geo_path, "r", encoding="utf-8") as f:
    geo = json.load(f)

for feat in geo.get("features", []):
    c = feat.get("properties", {}).get("code", "").strip().upper()
    if c in ["NZM", "HNZM", "SGO", "SAGO", "JHS", "VGLJ"]:
        print(f"GeoJSON has {c}: {feat.get('properties', {}).get('name')}")
