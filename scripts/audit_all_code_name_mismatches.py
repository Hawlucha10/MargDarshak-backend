import json
from collections import defaultdict

with open("D:/Sih58/NishkarshFoundData/TAG_2026_complete_timetable.json", "r", encoding="utf-8") as f:
    trains = json.load(f)

# Collect (code, normalized name) pairs
code_names = defaultdict(lambda: defaultdict(int))
for t in trains:
    for s in t["stops"]:
        c = s["station_code"].upper().strip()
        n = (s.get("station_name") or "").strip()
        if c and n:
            code_names[c][n] += 1

print(f"Total station codes: {len(code_names)}")

# Look for patterns where code doesn't match standard station
KNOWN_FIXES = {
    "INDM": "INDB",       # Indore Jn BG
    "ADIJ": "ADI",        # Ahmedabad Jn
    "CPNL": "CNB",        # Kanpur Central
    "RTLM": "RTM",        # Ratlam Jn
    "MALA": "RKMP",       # Rani Kamalapati
    "RAYA": "SMVB",       # Sir M. Visvesvaraya Terminal Bengaluru
    "BELA": "BGM",        # Belagavi
    "RAMA": "RDM",        # Ramagundam
    "APTA": "MCTM",       # Martyr Captain Tushar Mahajan
    "ADRA": "BHC",        # Bhadrak (when name is Bhadrak)
    "HAPA": "VSKP",       # Visakhapatnam (when name is Visakhapatnam)
    "MBAN": "AADR",       # Amb Andaura
    "AJAH": "RJY",        # Rajahmundry
    "HMUN": "RJY",        # Rajahmundry
    "ANGA": "GGC",        # Gangapur City
    "SAI":  "DEE",        # Delhi Sarai Rohilla
    "CP":   "KOAA",       # Kolkata
}

# Print top 40 codes by count and their names
for c in sorted(code_names.keys(), key=lambda x: -sum(code_names[x].values()))[:50]:
    names_top = sorted(code_names[c].items(), key=lambda x: -x[1])[:2]
    total = sum(code_names[c].values())
    print(f"{c:6s} (total {total:3d}): {names_top}")
