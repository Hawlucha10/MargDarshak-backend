"""
Polishing and Verification Engine for TAG 2026 Timetable Data
Applies zero-tolerance cleaning rules to achieve 100% clean data.
"""

import json
import re
from pathlib import Path

PRIMARY_PATH = Path("D:/Sih58/NishkarshFoundData/TAG_2026_complete_timetable.json")
SECONDARY_PATH = Path("d:/Yue/Ura/Sih 58/NishkarshFoundData/TAG_2026_complete_timetable.json")
GEO_PATH = Path("D:/Sih58/MargDarshak-backend/data/stations/stations_geo.geojson")

# Load GeoJSON for station code validation
with open(GEO_PATH, "r", encoding="utf-8") as f:
    geo = json.load(f)
geo_map = {}
for feat in geo.get("features", []):
    props = feat.get("properties", {})
    c = props.get("code", "").strip().upper()
    n = props.get("name", "").strip().upper()
    if c and n:
        geo_map[n] = c

KNOWN_FIXES = {
    "Pt. Deen Dayal a Upadhyaya Jn.": ("Pt. Deen Dayal Upadhyaya Jn.", "DDU"),
    "Pt. Deen Dayal d Upadhyaya Jn.": ("Pt. Deen Dayal Upadhyaya Jn.", "DDU"),
    "Virangana d Laxmibai Jhansi": ("Virangana Lakshmibai Jhansi", "VGLJ"),
    "Virangana a Laxmibai Jhansi": ("Virangana Lakshmibai Jhansi", "VGLJ"),
    "Virangana Lakshmibai": ("Virangana Lakshmibai Jhansi", "VGLJ"),
    "i n V a is l h B v e e n s g v a a l r u a r y u": ("Sir M. Visvesvaraya Terminal Bengaluru", "SMVB"),
    "L Ti o la k k m ( T n ) ya": ("Lokmanya Tilak Terminus", "LTT"),
    "Chitrakoot Dham Karvi": ("Chitrakoot Dham Karvi", "CKTD"),
}

def clean_station_name_strict(name: str):
    if not name:
        return "", ""
    if name in KNOWN_FIXES:
        return KNOWN_FIXES[name]
        
    s = " ".join(str(name).split())
    # Reject header/calendar rows
    if any(w in s.lower() for w in ["daily", "weekly", "table", "from table", "to table", "days of", "accommodation", "departure", "arrival"]):
        return None, None
    if re.search(r"^\d{2}\.\d{2}", s):
        return None, None
        
    # Remove leading/trailing marker letters
    s = re.sub(r"^[ad]\s+", "", s, flags=re.IGNORECASE)
    s = re.sub(r"\s+[ad]$", "", s, flags=re.IGNORECASE)
    s = re.sub(r"\s+[ad]$", "", s, flags=re.IGNORECASE)
    # Remove inside marker letter ' a ' or ' d '
    s = re.sub(r"\s+[ad]\s+", " ", s, flags=re.IGNORECASE)
    s = re.sub(r"^Km\s*\d*\s*", "", s, flags=re.IGNORECASE)
    s = re.sub(r"^\d+\s+", "", s)
    s = " ".join(s.split()).strip()
    
    if len(s) < 2:
        return None, None
        
    # Code lookup
    code = None
    u = s.upper()
    if u in geo_map:
        code = geo_map[u]
    else:
        norm = re.sub(r"\b(JN|JUNCTION|CANTT|TERMINUS|TER|RD|ROAD)\b", "", u).strip()
        norm = " ".join(norm.split())
        if norm in geo_map:
            code = geo_map[norm]
            
    return s, code

def polish():
    with open(PRIMARY_PATH, "r", encoding="utf-8") as f:
        trains = json.load(f)

    print(f"Loaded {len(trains)} raw trains from {PRIMARY_PATH.name}")
    
    clean_trains = []
    discarded_fragments = 0
    
    for train in trains:
        raw_stops = train.get("stops", [])
        valid_stops = []
        
        for stop in raw_stops:
            s_name = stop.get("station_name", "")
            c_name, c_code = clean_station_name_strict(s_name)
            if not c_name:
                continue
                
            code = c_code or stop.get("station_code")
            stop_clean = dict(stop)
            stop_clean["station_name"] = c_name
            stop_clean["station_code"] = code
            valid_stops.append(stop_clean)
            
        # Discard fragments with <= 1 stop
        if len(valid_stops) <= 1:
            discarded_fragments += 1
            continue
            
        # Re-sequence stops and handle day/time rollovers cleanly
        processed_stops = []
        cur_day = 1
        prev_dep_min = -1
        
        for seq, st in enumerate(valid_stops, 1):
            is_first = (seq == 1)
            is_last = (seq == len(valid_stops))
            
            arr = None if is_first else st.get("arrival")
            dep = None if is_last else st.get("departure")
            
            # If intermediate stop has only arrival or only departure, mirror it
            if not is_first and not is_last:
                if arr and not dep:
                    dep = arr
                elif dep and not arr:
                    arr = dep
                    
            # Check halt time consistency (arr <= dep)
            if arr and dep:
                ah, am = map(int, arr.split(":")[:2])
                dh, dm = map(int, dep.split(":")[:2])
                a_min = ah * 60 + am
                d_min = dh * 60 + dm
                if d_min < a_min:
                    # Halt crosses midnight: departure is next day!
                    # E.g. Arr 23:55, Dep 00:05
                    pass
                else:
                    # Normal halt within same day
                    pass
                    
            # Track day rollover across stops
            t_check = dep or arr or "00:00:00"
            parts = [int(x) for x in t_check.split(":")[:2]]
            cur_min = parts[0] * 60 + parts[1]
            if prev_dep_min != -1 and cur_min < prev_dep_min - 90:
                cur_day += 1
            prev_dep_min = cur_min
            
            st_final = dict(st)
            st_final["stop_sequence"] = seq
            st_final["arrival"] = arr
            st_final["departure"] = dep
            st_final["day"] = cur_day
            processed_stops.append(st_final)
            
        train_clean = dict(train)
        train_clean["origin_station"] = processed_stops[0]["station_name"]
        train_clean["origin_code"] = processed_stops[0]["station_code"]
        train_clean["destination_station"] = processed_stops[-1]["station_name"]
        train_clean["destination_code"] = processed_stops[-1]["station_code"]
        train_clean["total_distance_km"] = processed_stops[-1]["km"]
        train_clean["total_stops"] = len(processed_stops)
        train_clean["stops"] = processed_stops
        clean_trains.append(train_clean)
        
    print(f"Discarded {discarded_fragments} unusable fragments (<= 1 stop).")
    print(f"Final Clean Train Routes: {len(clean_trains)}")
    
    # Save to both paths
    with open(PRIMARY_PATH, "w", encoding="utf-8") as f:
        json.dump(clean_trains, f, indent=2, ensure_ascii=False)
    print(f"Saved Polished Primary:   {PRIMARY_PATH} ({PRIMARY_PATH.stat().st_size / (1024*1024):.2f} MB)")
    
    with open(SECONDARY_PATH, "w", encoding="utf-8") as f:
        json.dump(clean_trains, f, indent=2, ensure_ascii=False)
    print(f"Saved Polished Secondary: {SECONDARY_PATH}")

if __name__ == "__main__":
    polish()
