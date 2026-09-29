"""
Unified High-Precision Timetable Extractor Prototype
Tests on Tables: 01, 02, 06, 12, 56
"""

import json
import re
import math
from pathlib import Path
import pdfplumber
import pypdf

BASE_DIR = Path("D:/Sih58/NishkarshFoundData")
TABLES_DIR = BASE_DIR / "Content" / "T"
GEO_PATH = Path("D:/Sih58/MargDarshak-backend/data/stations/stations_geo.geojson")
STN_INDEX_PDF = BASE_DIR / "Content" / "Station_Code_Index.pdf"
TRAIN_INDEX_PDF = BASE_DIR / "Content" / "Trains_Number_Index.pdf"

# 1. Load Station DB
def build_station_database():
    stn_map = {}
    if GEO_PATH.exists():
        with open(GEO_PATH, "r", encoding="utf-8") as f:
            geo_data = json.load(f)
        for feat in geo_data.get("features", []):
            props = feat.get("properties", {})
            geom = feat.get("geometry", {})
            coords = geom.get("coordinates", [0, 0])
            code = props.get("code", "").strip().upper()
            name = props.get("name", "").strip().upper()
            if code and name:
                stn_map[name] = {"code": code, "lon": coords[0], "lat": coords[1]}
                clean_n = re.sub(r"\b(JN|JUNCTION|CANTT|TERMINUS|TER|RD|ROAD)\b", "", name).strip()
                clean_n = " ".join(clean_n.split())
                if clean_n and clean_n not in stn_map:
                    stn_map[clean_n] = {"code": code, "lon": coords[0], "lat": coords[1]}

    if STN_INDEX_PDF.exists():
        reader = pypdf.PdfReader(str(STN_INDEX_PDF))
        all_lines = []
        for p in reader.pages:
            for l in p.extract_text().split("\n"):
                if l.strip():
                    all_lines.append(l.strip())
        
        idx = 0
        while idx < len(all_lines):
            line = all_lines[idx]
            m = re.match(r"^(.*?)\s+([A-Z0-9/]{1,8})$", line)
            if m:
                name, code = m.group(1).strip().upper(), m.group(2).strip().upper()
                if "/" in code:
                    code = code.split("/")[0]
                if name not in stn_map:
                    stn_map[name] = {"code": code, "lon": None, "lat": None}
                idx += 1
            else:
                if idx + 1 < len(all_lines):
                    next_line = all_lines[idx + 1]
                    m2 = re.match(r"^(.*?)\s+([A-Z0-9/]{1,8})$", next_line)
                    if m2:
                        comb_name = (line + " " + m2.group(1)).strip().upper()
                        code = m2.group(2).strip().upper()
                        if "/" in code:
                            code = code.split("/")[0]
                        stn_map[comb_name] = {"code": code, "lon": None, "lat": None}
                        idx += 2
                        continue
                idx += 1

    aliases = {
        "MUMBAI CSMT": ("CSMT", 18.9401, 72.8356),
        "C SHIVAJI MAHARAJ T": ("CSMT", 18.9401, 72.8356),
        "CHHATRAPATI SHIVAJI MAHARAJ TERMINUS": ("CSMT", 18.9401, 72.8356),
        "VIRANGANA LAKSHMIBAI JHANSI": ("VGLJ", 25.4484, 78.5685),
        "V L JHANSI": ("VGLJ", 25.4484, 78.5685),
        "LOKMANYA TILAK": ("LTT", 19.0694, 72.8906),
        "LOKMANYA TILAK (T)": ("LTT", 19.0694, 72.8906),
        "AYODHYA DHAM": ("AY", 26.7997, 82.1998),
        "AYODHYA CANTT": ("AYC", 26.7756, 82.1332),
        "PRAYAGRAJ": ("PRYJ", 25.4358, 81.8263),
        "RANI KAMALAPATI": ("RKMP", 23.2037, 77.4394),
        "CHHATARPUR": ("MCSC", 24.9184, 79.5936),
        "NEW DELHI": ("NDLS", 28.6431, 77.2197),
        "DELHI": ("DLI", 28.6606, 77.2289),
        "HAZRAT NIZAMUDDIN": ("NZM", 28.5888, 77.2534),
        "NIZAMUDDIN": ("NZM", 28.5888, 77.2534),
        "SIR M VISVESVARAYA TERMINAL": ("SMVB", 13.0033, 77.6539),
        "CHHATRAPATI SHAHU MAHARAJ TERMINUS": ("KOP", 16.7028, 74.2408),
    }
    for k, (c, lat, lon) in aliases.items():
        stn_map[k] = {"code": c, "lat": lat, "lon": lon}
    return stn_map

def load_train_index():
    train_map = {}
    if TRAIN_INDEX_PDF.exists():
        reader = pypdf.PdfReader(str(TRAIN_INDEX_PDF))
        for p in reader.pages:
            for line in p.extract_text().split("\n"):
                m = re.search(r"(\d{5})(?:/(\d{5}))?\s+(.+)", line)
                if m:
                    t1, t2, rest = m.group(1), m.group(2), m.group(3).strip()
                    train_map[t1] = rest
                    if t2:
                        train_map[t2] = rest
    return train_map

STATION_DB = build_station_database()
TRAIN_DB = load_train_index()

GARBLED_LOOKUP = {
    "V L Jh ir k s n n h s g m i an ib a i a": "Virangana Lakshmibai Jhansi",
    "V L Jh ir k s n n h s g m i n ib a i a": "Virangana Lakshmibai Jhansi",
    "L Ti o la k k m ( T n ) ya": "Lokmanya Tilak Terminus",
    "i n V is l h B v e e n s g v a l r u r y u a": "Sir M. Visvesvaraya Terminal Bengaluru",
    "0 C M h h h a t r r a j p (T at ) i Shahu": "Chhatrapati Shahu Maharaj Terminus",
    "S va ir r M y V i T s e h r v m e i s n - al": "Sir M. Visvesvaraya Terminal Bengaluru",
}

def clean_station_name(raw: str):
    if not raw:
        return ""
    for g_str, canon in GARBLED_LOOKUP.items():
        if g_str in raw:
            return canon
    s = " ".join(str(raw).split())
    s = re.sub(r"^Km\s*\d*\s*", "", s, flags=re.IGNORECASE)
    s = re.sub(r"^\d+\s+", "", s)
    s = re.sub(r"^(?:[ad\./\-])+\s+", "", s, flags=re.IGNORECASE)
    s = re.sub(r"\s+(?:[ad\./\-])+$", "", s, flags=re.IGNORECASE)
    s = re.sub(r"\s+[ad]$", "", s, flags=re.IGNORECASE)
    s = re.sub(r"\s+[ad]$", "", s, flags=re.IGNORECASE)
    return s.strip()

def resolve_station(name_raw: str):
    clean_name = clean_station_name(name_raw)
    if not clean_name or len(clean_name) < 2:
        return None, None, None, None
    u_name = clean_name.upper()
    if u_name in STATION_DB:
        entry = STATION_DB[u_name]
        return clean_name, entry["code"], entry.get("lat"), entry.get("lon")
    norm = re.sub(r"\b(JN|JUNCTION|CANTT|TERMINUS|TER|RD|ROAD)\b", "", u_name).strip()
    norm = " ".join(norm.split())
    if norm in STATION_DB:
        entry = STATION_DB[norm]
        return clean_name, entry["code"], entry.get("lat"), entry.get("lon")
    for k, v in STATION_DB.items():
        if len(k) >= 4 and (k == u_name or k in u_name or u_name in k):
            return clean_name, v["code"], v.get("lat"), v.get("lon")
    clean_alpha = re.sub(r"[^A-Z]", "", u_name)
    return clean_name, clean_alpha[:4] if clean_alpha else "STN", None, None

def haversine_dist(lat1, lon1, lat2, lon2):
    if not (lat1 and lon1 and lat2 and lon2):
        return None
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return int(round(R * c * 1.15))

def parse_time_cell(cell_val: str):
    if not cell_val:
        return []
    s = str(cell_val).strip()
    if "..." in s or s in (". .", "-", "None", ""):
        return []
    # Find all times
    # In table cells, arrival is line 1, departure is line 2
    lines = [l.strip() for l in s.split("\n") if l.strip()]
    tokens = []
    for l in lines:
        m = re.findall(r"\b(\d{1,2})[.:](\d{2})\b", l)
        for h, mn in m:
            tokens.append(f"{int(h):02d}:{mn}")
    return tokens

def parse_table_file(pdf_path: Path):
    table_trains = []
    t_num_str = pdf_path.stem.replace("Table_", "")
    
    with pdfplumber.open(str(pdf_path)) as pdf:
        for p_idx, page in enumerate(pdf.pages):
            words = page.extract_words()
            if not words:
                continue
                
            # Find train numbers in header
            train_num_words = [w for w in words if re.search(r"^\d{5}", w["text"]) and w["top"] < 160]
            if not train_num_words:
                train_num_words = [w for w in words if re.search(r"^\d{5}", w["text"]) and w["top"] < 220]
            if not train_num_words:
                continue
                
            # Detect layout: MIDDLE vs LEFT
            label_words = [w for w in words if "train" in w["text"].lower() and w["top"] < 200]
            header_x = min(w["x0"] for w in label_words) if label_words else 0
            is_middle = (header_x > 120)
            
            # If middle layout, find km / station boundary
            # Train words sorted by x0
            train_num_words = sorted(train_num_words, key=lambda w: w["x0"])
            
            # For each train number word, define its column slice
            # To avoid crosstalk, each train gets an explicit vertical column
            train_cols = []
            for i, tw in enumerate(train_num_words):
                t_num = re.search(r"(\d{5})", tw["text"]).group(1)
                # left bound
                if i == 0:
                    left_b = tw["x0"] - 6
                else:
                    left_b = (train_num_words[i-1]["x1"] + tw["x0"]) / 2.0
                # right bound
                if i == len(train_num_words) - 1:
                    right_b = tw["x1"] + 6
                else:
                    right_b = (tw["x1"] + train_num_words[i+1]["x0"]) / 2.0
                    
                direction = "DOWN"
                if is_middle and tw["x0"] > header_x:
                    direction = "UP"
                elif is_middle and tw["x0"] < header_x:
                    direction = "DOWN"
                    
                train_cols.append({
                    "train_number": t_num,
                    "x0": left_b,
                    "x1": right_b,
                    "top": tw["top"],
                    "direction": direction
                })

            # Now find station column boundaries
            if not is_middle:
                stn_x0 = 0
                stn_x1 = train_cols[0]["x0"]
            else:
                # station column is between down trains and up trains
                down_trains = [tc for tc in train_cols if tc["direction"] == "DOWN"]
                up_trains = [tc for tc in train_cols if tc["direction"] == "UP"]
                stn_x0 = down_trains[-1]["x1"] if down_trains else 0
                stn_x1 = up_trains[0]["x0"] if up_trains else page.width

            # Extract table with pdfplumber using explicit vertical lines
            # v_lines = [stn_x0, stn_x1] + [tc['x0'] for tc in train_cols] + [train_cols[-1]['x1']]
            # To maintain simplicity and accuracy: use default extract_tables, but parse times from train_cols
            table_raw = page.extract_tables()[0]
            if not table_raw:
                continue
                
            # Scan rows to find station rows
            # Find which column in table_raw is the station column
            stn_col_idx = 0
            km_col_idx = None
            for c_idx in range(len(table_raw[0])):
                col_text = " ".join(str(table_raw[r][c_idx] or "") for r in range(min(15, len(table_raw)))).lower()
                if "km" in col_text:
                    km_col_idx = c_idx
                if any(x in col_text for x in ["station", "junction", "delhi", "mumbai", "howrah", "chennai"]):
                    stn_col_idx = c_idx
            if km_col_idx is not None and stn_col_idx == km_col_idx:
                stn_col_idx = km_col_idx + 1

            # Match train cols to table_raw columns
            # Find train row in table_raw
            train_row_idx = None
            for r_idx in range(min(6, len(table_raw))):
                row_str = " ".join(str(c or "") for c in table_raw[r_idx])
                if any(tc["train_number"] in row_str for tc in train_cols):
                    train_row_idx = r_idx
                    break
            if train_row_idx is None:
                continue

            # Map each train number to its column index in table_raw
            train_col_mapping = {}
            for c_idx in range(len(table_raw[train_row_idx])):
                cell_text = str(table_raw[train_row_idx][c_idx] or "")
                for tc in train_cols:
                    if tc["train_number"] in cell_text and tc["train_number"] not in train_col_mapping:
                        train_col_mapping[tc["train_number"]] = {
                            "col_idx": c_idx,
                            "direction": tc["direction"]
                        }

            # Collect station rows
            station_rows = []
            for r_idx in range(train_row_idx + 1, len(table_raw)):
                raw_stn = table_raw[r_idx][stn_col_idx]
                c_name, code, lat, lon = resolve_station(raw_stn)
                if not c_name or any(k in c_name.lower() for k in ["table", "days of", "operation", "accommodation"]):
                    continue
                
                track_km = None
                if km_col_idx is not None and km_col_idx < len(table_raw[r_idx]):
                    km_cell = str(table_raw[r_idx][km_col_idx] or "")
                    m_km = re.search(r"(\d+)", km_cell)
                    if m_km:
                        track_km = int(m_km.group(1))

                station_rows.append({
                    "row_idx": r_idx,
                    "station_name": c_name,
                    "station_code": code,
                    "lat": lat,
                    "lon": lon,
                    "track_km": track_km
                })

            if not station_rows:
                continue

            # Now extract stops for each train mapped
            for t_num, t_info in train_col_mapping.items():
                c_idx = t_info["col_idx"]
                dirn = t_info["direction"]
                t_name = TRAIN_DB.get(t_num, f"Train {t_num}")

                stn_list = station_rows if dirn == "DOWN" else list(reversed(station_rows))
                raw_stops = []

                for stn in stn_list:
                    cell_val = str(table_raw[stn["row_idx"]][c_idx] or "")
                    tokens = parse_time_cell(cell_val)
                    if not tokens:
                        continue

                    # Arrival and departure assignment
                    if len(tokens) >= 2:
                        # If two tokens are on separate lines, line 0 is Arr, line 1 is Dep
                        # In DOWN: arr <= dep
                        t1, t2 = tokens[0], tokens[1]
                        if dirn == "DOWN":
                            arr_t, dep_t = t1, t2
                        else:
                            # In UP: Token 1 is Dep, Token 2 is Arr (or check line order)
                            dep_t, arr_t = t1, t2
                    else:
                        arr_t, dep_t = tokens[0], tokens[0]

                    # Negative halt check & fix:
                    # If dep_t < arr_t within same hour or daylight, swap them
                    h1, m1 = map(int, arr_t.split(":"))
                    h2, m2 = map(int, dep_t.split(":"))
                    if h2 * 60 + m2 < h1 * 60 + m1:
                        # If difference is <= 60 mins, they were swapped in UP/DOWN layout
                        if (h1 * 60 + m1) - (h2 * 60 + m2) < 60:
                            arr_t, dep_t = dep_t, arr_t

                    raw_stops.append({
                        "station_name": stn["station_name"],
                        "station_code": stn["station_code"],
                        "lat": stn["lat"],
                        "lon": stn["lon"],
                        "track_km": stn["track_km"],
                        "arr_t": arr_t,
                        "dep_t": dep_t
                    })

                if not raw_stops:
                    continue

                # Build cumulative distance
                cum_km = 0
                prev_lat, prev_lon = None, None
                prev_track = None
                processed_stops = []
                current_day = 1
                prev_min = -1

                for seq, s in enumerate(raw_stops, 1):
                    is_first = (seq == 1)
                    is_last = (seq == len(raw_stops))

                    if is_first:
                        arr_val = None
                        dep_val = f"{s['dep_t']}:00"
                        cum_km = 0
                        prev_track = s["track_km"]
                        prev_lat, prev_lon = s["lat"], s["lon"]
                    elif is_last:
                        arr_val = f"{s['arr_t']}:00"
                        dep_val = None
                        step = 0
                        if s["track_km"] is not None and prev_track is not None and 0 < s["track_km"] - prev_track < 300:
                            step = s["track_km"] - prev_track
                        else:
                            h_dist = haversine_dist(prev_lat, prev_lon, s["lat"], s["lon"])
                            step = h_dist if (h_dist and 0 < h_dist < 300) else 40
                        cum_km += max(1, step)
                    else:
                        arr_val = f"{s['arr_t']}:00"
                        dep_val = f"{s['dep_t']}:00"
                        step = 0
                        if s["track_km"] is not None and prev_track is not None and 0 < s["track_km"] - prev_track < 300:
                            step = s["track_km"] - prev_track
                            prev_track = s["track_km"]
                        else:
                            h_dist = haversine_dist(prev_lat, prev_lon, s["lat"], s["lon"])
                            step = h_dist if (h_dist and 0 < h_dist < 300) else 35
                            prev_track = (prev_track or 0) + step
                        cum_km += max(1, step)
                        prev_lat, prev_lon = s["lat"], s["lon"]

                    # Day rollover
                    t_str = s["dep_t"] or s["arr_t"]
                    try:
                        hh, mm = map(int, t_str.split(":"))
                        t_min = hh * 60 + mm
                        if prev_min != -1 and t_min < prev_min - 90:
                            current_day += 1
                        prev_min = t_min
                    except Exception:
                        pass

                    processed_stops.append({
                        "stop_sequence": seq,
                        "station_code": s["station_code"],
                        "station_name": s["station_name"],
                        "km": cum_km,
                        "arrival": arr_val,
                        "departure": dep_val,
                        "day": current_day
                    })

                table_trains.append({
                    "train_number": t_num,
                    "train_name": t_name,
                    "table_number": t_num_str,
                    "direction": dirn,
                    "origin_station": processed_stops[0]["station_name"],
                    "origin_code": processed_stops[0]["station_code"],
                    "destination_station": processed_stops[-1]["station_name"],
                    "destination_code": processed_stops[-1]["station_code"],
                    "total_distance_km": processed_stops[-1]["km"],
                    "total_stops": len(processed_stops),
                    "stops": processed_stops
                })

    return table_trains

if __name__ == "__main__":
    print("=== TESTING ON TABLES 01, 02, 06, 12, 56 ===")
    sample_tables = [1, 2, 6, 12, 56]
    all_sample_trains = []
    for t in sample_tables:
        pdf_file = TABLES_DIR / f"Table_{t:02d}.pdf"
        trains = parse_table_file(pdf_file)
        print(f"Table {t:02d}: Extracted {len(trains)} trains")
        all_sample_trains.extend(trains)

    # Quick audit on sample trains
    neg_halts = 0
    garbled_cnt = 0
    trail_cnt = 0
    non_mono = 0

    for tr in all_sample_trains:
        p_km = -1
        for st in tr["stops"]:
            if st["km"] < p_km:
                non_mono += 1
            p_km = st["km"]
            sname = st["station_name"]
            if re.search(r"\b[ad]\b", sname) or sname.endswith(" a") or sname.endswith(" d"):
                trail_cnt += 1
            if re.search(r"\b[a-zA-Z]\s+[a-zA-Z]\s+[a-zA-Z]\b", sname):
                garbled_cnt += 1
            if st["arrival"] and st["departure"]:
                a_h, a_m = map(int, st["arrival"].split(":")[:2])
                d_h, d_m = map(int, st["departure"].split(":")[:2])
                if d_h * 60 + d_m < a_h * 60 + a_m:
                    neg_halts += 1
                    print(f"  [NEG HALT] Train {tr['train_number']} (T{tr['table_number']}) at {sname}: Arr {st['arrival']} > Dep {st['departure']}")

    print("\n" + "=" * 50)
    print(f"SAMPLE AUDIT RESULTS ({len(all_sample_trains)} trains):")
    print(f"  Negative halts: {neg_halts}")
    print(f"  Garbled names:  {garbled_cnt}")
    print(f"  Trailing marks: {trail_cnt}")
    print(f"  Non-monotonic:  {non_mono}")
    print("=" * 50)
