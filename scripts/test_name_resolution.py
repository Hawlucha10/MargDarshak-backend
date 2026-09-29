import json
import re

with open("D:/Sih58/NishkarshFoundData/TAG_2026_complete_timetable.json", "r", encoding="utf-8") as f:
    trains = json.load(f)

with open("D:/Sih58/MargDarshak-backend/data/stations/stations_geo.geojson", "r", encoding="utf-8") as f:
    geo = json.load(f)

# Build a lookup of clean name -> official code from GeoJSON
geo_name_to_code = {}
geo_code_to_name = {}
for feat in geo.get("features", []):
    props = feat.get("properties", {})
    c = props.get("code", "").strip().upper()
    n = props.get("name", "").strip().upper()
    if c and n:
        geo_name_to_code[n] = c
        geo_code_to_name[c] = n

# Canonical overrides for known major stations
EXPLICIT_NAME_MAP = {
    "PRAYAGRAJ": "PRYJ",
    "PRAYAGRAJ JN": "PRYJ",
    "PRAYAGRAJ CHHEOKI": "PCOI",
    "PRAYAGRAJ RAMBAGH": "PRRB",
    "AGRA CANTT": "AGC",
    "AGRA CANTT.": "AGC",
    "AGRA FORT": "AF",
    "VIZIANAGARAM": "VZM",
    "VIZIANAGARAM JN": "VZM",
    "VIRUDUNAGAR": "VPT",
    "VIRUDUNAGAR JN": "VPT",
    "VIRUDUNAGAR JN.": "VPT",
    "VISAKHAPATNAM": "VSKP",
    "SAKHAPATNAM": "VSKP",
    "HAPA": "HAPA",
    "ANAND VIHAR (T)": "ANVT",
    "ANAND VIHAR TRM": "ANVT",
    "ANAND": "ANND",
    "THIRUVANANTHAPURAM": "TVC",
    "THIRUVANANTHAPURAM CENTRAL": "TVC",
    "HAPUR": "HPU",
    "SURAT": "ST",
    "SURATKAL": "SL",
    "INDORE": "INDB",
    "INDORE JN": "INDB",
    "INDORE JN BG": "INDB",
    "AHMEDABAD": "ADI",
    "AHMEDABAD JN": "ADI",
    "RANI KAMLAPATI": "RKMP",
    "RANI KAMALAPATI": "RKMP",
    "RATLAM": "RTM",
    "RATLAM JN": "RTM",
    "KANPUR": "CNB",
    "KANPUR CENTRAL": "CNB",
    "KANPUR ANWARGANJ": "CPA",
    "BELAGAVI": "BGM",
    "RAMAGUNDAM": "RDM",
    "DELHI": "DLI",
    "EW DELHI": "NDLS",
    "NEW DELHI": "NDLS",
    "DELHI CANTT": "DEC",
    "DELHI CANTT.": "DEC",
    "DELHI SARAI ROHILLA": "DEE",
    "DELHI SARAI ROHILLAD": "DEE",
    "KOLKATA": "KOAA",
    "HOWRAH": "HWH",
    "HOWRAH JN": "HWH",
    "SEALDAH": "SDAH",
    "GANGAPUR CITY": "GGC",
    "ANGAPUR ITY": "GGC",
    "AMB ANDAURA": "AADR",
    "MB ANDAURA": "AADR",
    "RAJAHMUNDRY": "RJY",
    "RAJAHMUNDARY": "RJY",
    "HMUNDRY": "RJY",
    "AJAHMUNDARY": "RJY",
    "BHADRAK": "BHC",
    "JABALPUR": "JBP",
    "GWALIOR": "GWL",
    "PUNE": "PUNE",
    "PUNE JN": "PUNE",
    "BHOPAL": "BPL",
    "ITSI": "ET",
    "ITARSI": "ET",
    "NAGPUR": "NGP",
    "MATHURA": "MTJ",
    "MATHURA JN": "MTJ",
    "LALITPUR": "LAR",
    "LALITPUR JN": "LAR",
    "BINA": "BINA",
    "BINA JN": "BINA",
    "BINA MALKHEDI": "MAKR",
    "SAUGOR": "SGO",
    "SAGOUR": "SGO",
    "DAMOH": "DMO",
    "KATNI": "KTE",
    "KATNI MURWARA": "KMZ",
}

# Scan all stops and see what changes
updates = []
for t in trains:
    for s in t["stops"]:
        name = (s.get("station_name") or "").strip()
        curr_code = s.get("station_code", "").strip().upper()
        clean_name = re.sub(r"^\d+", "", name).strip().upper()

        correct_code = None
        for k, v in EXPLICIT_NAME_MAP.items():
            if clean_name == k or clean_name.startswith(k):
                correct_code = v
                break

        if correct_code and correct_code != curr_code:
            updates.append((t["train_number"], name, curr_code, correct_code))

print(f"Total stops to correct: {len(updates)}")
sample_updates = {}
for u in updates:
    k = (u[1], u[2], u[3])
    sample_updates[k] = sample_updates.get(k, 0) + 1

for (name, old_c, new_c), count in sorted(sample_updates.items(), key=lambda x: -x[1])[:30]:
    print(f"  {name:30s} | {old_c:6s} -> {new_c:6s} ({count:3d} stops)")
