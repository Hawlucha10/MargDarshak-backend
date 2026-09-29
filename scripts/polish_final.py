"""
Final In-Memory Polisher for TAG 2026 Timetable
Zero-tolerance cleanup for remaining edge cases.
"""

import json
import re
from pathlib import Path

PRIMARY = Path("D:/Sih58/NishkarshFoundData/TAG_2026_complete_timetable.json")
SECONDARY = Path("d:/Yue/Ura/Sih 58/NishkarshFoundData/TAG_2026_complete_timetable.json")
GEO_PATH = Path("D:/Sih58/MargDarshak-backend/data/stations/stations_geo.geojson")

with open(GEO_PATH, "r", encoding="utf-8") as f:
    geo = json.load(f)
geo_map = {}
for feat in geo.get("features", []):
    props = feat.get("properties", {})
    c = props.get("code", "").strip().upper()
    n = props.get("name", "").strip().upper()
    if c and n:
        geo_map[n] = c
        clean_n = re.sub(r"\b(JN|JUNCTION|CANTT|TERMINUS|TER|RD|ROAD)\b", "", n).strip()
        clean_n = " ".join(clean_n.split())
        if clean_n and clean_n not in geo_map:
            geo_map[clean_n] = c

ALIASES = {
    "PUNE": "PUNE", "KOTA": "KOTA", "DURG": "DURG", "TATA": "TATA", "TATANAGAR": "TATA",
    "KIUL": "KIUL", "BINA": "BINA", "GAYA": "GAYA", "BEAS": "BEAS", "ARA": "ARA", "MAU": "MAU",
    "LUNI": "LUNI", "MURI": "MURI", "ADRA": "ADRA", "CHITRAKOOT DHAM KARVI": "CKTD",
    "BATHINDA": "BTI", "JODHPUR": "JU", "JAIPUR": "JP", "DEGANA": "DNA", "MAKRANA": "MKN",
    "GUNTUR": "GNT", "NANDYAL": "NDL", "PHULERA": "FL", "VIJAYAWADA": "BZA", "SURATGARH": "SOG",
    "HANUMANGARH": "HMH", "RAJPURA": "RPJ", "PATIALA": "PTA", "DHURI": "DUI",
    "VIRANGANA LAKSHMIBAI JHANSI": "VGLJ", "LOKMANYA TILAK TERMINUS": "LTT",
    "CHHATRAPATI SHAHU MAHARAJ TERMINUS": "KOP", "SIR M. VISVESVARAYA TERMINAL BENGALURU": "SMVB",
    "PT. DEEN DAYAL UPADHYAYA JN.": "DDU"
}
geo_map.update(ALIASES)

def clean_station_name(name: str):
    if not name:
        return "", "STN"
    
    # Check garbled substrings
    if "Jh ir k s" in name:
        return "Virangana Lakshmibai Jhansi", "VGLJ"
    if "Ti o la" in name:
        return "Lokmanya Tilak Terminus", "LTT"
    if "M h h h" in name:
        return "Chhatrapati Shahu Maharaj Terminus", "KOP"
    if "va ir r M y" in name or "is l h B v" in name:
        return "Sir M. Visvesvaraya Terminal Bengaluru", "SMVB"
    if "Deen Dayal" in name:
        return "Pt. Deen Dayal Upadhyaya Jn.", "DDU"
    if "Laxmibai" in name or "Lakshmibai" in name:
        return "Virangana Lakshmibai Jhansi", "VGLJ"

    s = " ".join(str(name).split())
    # Strip leading markers like 'd ', 'a '
    s = re.sub(r"^[ad]\s+", "", s, flags=re.IGNORECASE)
    s = re.sub(r"\s+[ad]$", "", s, flags=re.IGNORECASE)
    s = re.sub(r"\s+[ad]$", "", s, flags=re.IGNORECASE)
    s = re.sub(r"\s+[ad]\s+", " ", s, flags=re.IGNORECASE)
    s = re.sub(r"^Km\s*\d*\s*", "", s, flags=re.IGNORECASE)
    s = re.sub(r"^\d+\s+", "", s)
    s = " ".join(s.split()).strip()

    u = s.upper()
    code = geo_map.get(u)
    if not code:
        norm = re.sub(r"\b(JN|JUNCTION|CANTT|TERMINUS|TER|RD|ROAD)\b", "", u).strip()
        norm = " ".join(norm.split())
        code = geo_map.get(norm)
    if not code:
        for k, v in geo_map.items():
            if len(k) >= 4 and (k == u or k in u or u in k):
                code = v
                break
    if not code:
        code = re.sub(r"[^A-Z]", "", u)[:4]

    return s, code

def main():
    with open(PRIMARY, "r", encoding="utf-8") as f:
        trains = json.load(f)

    print(f"Loaded {len(trains)} trains for final polish...")

    clean_trains = []
    fixed_halts = 0
    fixed_stns = 0

    for tr in trains:
        stops = tr.get("stops", [])
        if len(stops) <= 1:
            continue

        clean_stops = []
        cur_day = 1
        prev_dep_min = -1

        for idx, st in enumerate(stops, 1):
            is_first = (idx == 1)
            is_last = (idx == len(stops))

            raw_name = st.get("station_name", "")
            c_name, c_code = clean_station_name(raw_name)
            if c_name != raw_name:
                fixed_stns += 1

            arr = None if is_first else st.get("arrival")
            dep = None if is_last else st.get("departure")

            # Intermediate stop sanity
            if not is_first and not is_last:
                if arr and not dep:
                    dep = arr
                elif dep and not arr:
                    arr = dep

            # Halt time check & midnight day rollover
            if arr and dep:
                ah, am = map(int, arr.split(":")[:2])
                dh, dm = map(int, dep.split(":")[:2])
                a_min = ah * 60 + am
                d_min = dh * 60 + dm
                if d_min < a_min:
                    # Halt crosses midnight -> advance day
                    cur_day += 1
                    fixed_halts += 1

            t_chk = dep or arr or "00:00:00"
            parts = [int(x) for x in t_chk.split(":")[:2]]
            cur_min = parts[0] * 60 + parts[1]
            if prev_dep_min != -1 and cur_min < prev_dep_min - 90:
                cur_day += 1
            prev_dep_min = cur_min

            clean_stops.append({
                "stop_sequence": idx,
                "station_code": c_code,
                "station_name": c_name,
                "km": st.get("km", 0),
                "arrival": arr,
                "departure": dep,
                "day": cur_day
            })

        tr_clean = dict(tr)
        tr_clean["origin_station"] = clean_stops[0]["station_name"]
        tr_clean["origin_code"] = clean_stops[0]["station_code"]
        tr_clean["destination_station"] = clean_stops[-1]["station_name"]
        tr_clean["destination_code"] = clean_stops[-1]["station_code"]
        tr_clean["total_distance_km"] = clean_stops[-1]["km"]
        tr_clean["total_stops"] = len(clean_stops)
        tr_clean["stops"] = clean_stops
        clean_trains.append(tr_clean)

    print(f"Fixed {fixed_stns} station names and {fixed_halts} overnight halt rollovers!")
    print(f"Final Clean Trains: {len(clean_trains)}")

    with open(PRIMARY, "w", encoding="utf-8") as f:
        json.dump(clean_trains, f, indent=2, ensure_ascii=False)
    print(f"Saved Primary:   {PRIMARY} ({PRIMARY.stat().st_size / (1024*1024):.2f} MB)")

    with open(SECONDARY, "w", encoding="utf-8") as f:
        json.dump(clean_trains, f, indent=2, ensure_ascii=False)
    print(f"Saved Secondary: {SECONDARY}")

if __name__ == "__main__":
    main()
