"""
Test surgical updates to extract_all_tables logic on sample tables.
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
        "BANARAS": ("BSBS", 25.3176, 82.9691),
        "PT. DEEN DAYAL UPADHYAYA JN.": ("DDU", 25.2818, 83.1189),
    }
    for k, v in aliases.items():
        stn_map[k] = {"code": v[0], "lat": v[1], "lon": v[2]}
    return stn_map

STATION_DB = build_station_database()

GARBLED_LOOKUP = {
    "V L Jh ir k s n n h s g m i an ib a i a": "Virangana Lakshmibai Jhansi",
    "V L Jh ir k s n n h s g m i n ib a i a": "Virangana Lakshmibai Jhansi",
    "L Ti o la k k m ( T n ) ya": "Lokmanya Tilak Terminus",
    "i n V is l h B v e e n s g v a l r u r y u a": "Sir M. Visvesvaraya Terminal Bengaluru",
    "0 C M h h h a t r r a j p (T at ) i Shahu": "Chhatrapati Shahu Maharaj Terminus",
    "S va ir r M y V i T s e h r v m e i s n - al": "Sir M. Visvesvaraya Terminal Bengaluru",
    "Pt. Deen Dayal a Upadhyaya Jn.": "Pt. Deen Dayal Upadhyaya Jn.",
    "Pt. Deen Dayal d Upadhyaya Jn.": "Pt. Deen Dayal Upadhyaya Jn.",
    "Virangana d Laxmibai Jhansi": "Virangana Lakshmibai Jhansi",
    "Virangana a Laxmibai Jhansi": "Virangana Lakshmibai Jhansi",
}

def clean_station_name(raw: str) -> str:
    if not raw:
        return ""
    for g_str, canon in GARBLED_LOOKUP.items():
        if g_str in raw:
            return canon
    s = " ".join(str(raw).split())
    if any(k in s.lower() for k in ["table", "days of", "operation", "accommodation", "departure", "arrival"]):
        return ""
    if re.search(r"^\d{2}\.\d{2}", s):
        return ""
    s = re.sub(r"^Km\s*\d*\s*", "", s, flags=re.IGNORECASE)
    s = re.sub(r"^\d+\s+", "", s)
    s = re.sub(r"^[ad]\s+", "", s, flags=re.IGNORECASE)
    s = re.sub(r"\s+[ad]$", "", s, flags=re.IGNORECASE)
    s = re.sub(r"\s+[ad]$", "", s, flags=re.IGNORECASE)
    s = re.sub(r"\s+[ad]\s+", " ", s, flags=re.IGNORECASE)
    return " ".join(s.split()).strip()

def resolve_station(name_raw: str):
    clean = clean_station_name(name_raw)
    if not clean or len(clean) < 2:
        return None, None, None, None
    u = clean.upper()
    if u in STATION_DB:
        e = STATION_DB[u]
        return clean, e["code"], e.get("lat"), e.get("lon")
    norm = re.sub(r"\b(JN|JUNCTION|CANTT|TERMINUS|TER|RD|ROAD)\b", "", u).strip()
    norm = " ".join(norm.split())
    if norm in STATION_DB:
        e = STATION_DB[norm]
        return clean, e["code"], e.get("lat"), e.get("lon")
    for k, v in STATION_DB.items():
        if len(k) >= 4 and (k == u or k in u or u in k):
            return clean, v["code"], v.get("lat"), v.get("lon")
    return clean, re.sub(r"[^A-Z]", "", u)[:4], None, None

def haversine_km(lat1, lon1, lat2, lon2):
    if not (lat1 and lon1 and lat2 and lon2):
        return None
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return int(round(R * c * 1.15))

print("Testing clean_station_name on problem cases:")
test_cases = [
    "Itarsi a", "Bhusaval a", "Jabalpur a", "Kalyan a d",
    "Pt. Deen Dayal a Upadhyaya Jn.", "Virangana a Laxmibai Jhansi",
    "d Bathinda", "d Jodhpur", "V L Jh ir k s n n h s g m i an ib a i a"
]
for tc in test_cases:
    c_n, c_c, _, _ = resolve_station(tc)
    print(f"  '{tc}' -> '{c_n}' [{c_c}]")
