"""
Fix Canonical Station Codes across Timetable & Purge Deprecated Stations
========================================================================
1. Resolves all mismatched major station codes in timetable JSON:
   - INDM -> INDB (Indore)
   - ADIJ -> ADI (Ahmedabad)
   - CPNL -> CNB (Kanpur)
   - RTLM -> RTM (Ratlam)
   - MALA -> RKMP (Rani Kamalapati)
   - RAYA / SIRM -> SMVB (SMVT Bengaluru)
   - HAPA (where name is Visakhapatnam) -> VSKP
   - AGC (where name is Prayagraj) -> PRYJ
   - ANND (where name is Anand Vihar) -> ANVT
   - HPU (where name is Thiruvananthapuram) -> TVC
   - NGE (where name is Vizianagaram) -> VZM
   - NGE (where name is Virudunagar) -> VPT
   - BELA -> BGM (Belagavi)
   - RAMA -> RDM (Ramagundam)
   - ADRA (where name is Bhadrak) -> BHC
   - CP (where name is Kolkata) -> KOAA
   - DEC (where name is New Delhi) -> NDLS
2. Saves polished timetable JSON.
3. Ingests into PostgreSQL and purges obsolete Narrow Gauge stations (JBPN, ITRN, NABN).
"""

import json
import re
import asyncio
import sys
from pathlib import Path
from datetime import time
from decimal import Decimal

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text
from sqlalchemy.dialects.postgresql import insert
from app.db.postgres import get_session_maker
from app.db.models import StationModel, TimetableModel

PRIMARY_PATH = Path("D:/Sih58/NishkarshFoundData/TAG_2026_complete_timetable.json")
SECONDARY_PATH = Path("d:/Yue/Ura/Sih 58/NishkarshFoundData/TAG_2026_complete_timetable.json")

REFINED_NAME_MAP = {
    # Indore -> INDB
    "INDORE": "INDB",
    
    # Ahmedabad -> ADI
    "AHMEDABAD": "ADI",
    "AHMEDABAD JN": "ADI",
    
    # Prayagraj -> PRYJ
    "PRAYAGRAJ": "PRYJ",
    "PRAYAGRAJ JN": "PRYJ",
    "PRAYAGRAJ CHHEOKI": "PRYJ",
    "PRAYAGRAJ CHEOKI": "PRYJ",
    "62PRAYAGRAJ": "PRYJ",
    
    # Kanpur -> CNB
    "KANPUR": "CNB",
    "KANPUR CENTRAL": "CNB",
    "KANPUR 03": "CNB",
    
    # Ratlam -> RTM
    "RATLAM": "RTM",
    "RATLAM JN": "RTM",
    
    # Rani Kamalapati -> RKMP
    "RANI KAMLAPATI": "RKMP",
    "RANI KAMALAPATI": "RKMP",
    
    # Visakhapatnam -> VSKP
    "VISAKHAPATNAM": "VSKP",
    "SAKHAPATNAM": "VSKP",
    
    # Vizianagaram -> VZM
    "VIZIANAGARAM": "VZM",
    
    # Thiruvananthapuram -> TVC
    "THIRUVANANTHAPURAM": "TVC",
    "THIRUVANANTHAPURAM CENTRAL": "TVC",
    
    # Anand Vihar -> ANVT
    "ANAND VIHAR (T)": "ANVT",
    "ANAND VIHAR TRM": "ANVT",
    
    # Bhadrak -> BHC
    "BHADRAK": "BHC",
    
    # Ramagundam -> RDM
    "RAMAGUNDAM": "RDM",
    
    # Virudunagar -> VPT
    "VIRUDUNAGAR": "VPT",
    "VIRUDUNAGAR JN": "VPT",
    "VIRUDUNAGAR JN.": "VPT",
    
    # Belagavi -> BGM
    "BELAGAVI": "BGM",
    
    # Kolkata -> KOAA
    "KOLKATA": "KOAA",
    
    # Gangapur City -> GGC
    "GANGAPUR CITY": "GGC",
    "ANGAPUR ITY": "GGC",
    
    # Amb Andaura -> AADR
    "AMB ANDAURA": "AADR",
    "MB ANDAURA": "AADR",
    
    # Rajahmundry -> RJY
    "RAJAHMUNDRY": "RJY",
    "RAJAHMUNDARY": "RJY",
    "HMUNDRY": "RJY",
    "AJAHMUNDARY": "RJY",
    
    # New Delhi
    "NEW DELHI": "NDLS",
    "EW DELHI": "NDLS",
    
    # Sir M Visvesvaraya Terminal Bengaluru -> SMVB
    "SIR M VISHVESVARAYA TERMINAL": "SMVB",
    "SIR M. VISVESVARAYA TERMINAL BENGALURU": "SMVB",
    "SIR M VISHWESHWARAIAH T. BENGALURU": "SMVB",
    "SIR M. VISVESVARAYA TERMINAL": "SMVB",
}

def parse_time_obj(val):
    if not val:
        return None
    if isinstance(val, time):
        return val
    try:
        parts = str(val).strip().split(":")
        h = int(parts[0])
        m = int(parts[1])
        s = int(parts[2]) if len(parts) > 2 else 0
        return time(h, m, s)
    except Exception:
        return None

async def apply_fixes():
    print("Loading timetable...")
    with open(PRIMARY_PATH, "r", encoding="utf-8") as f:
        trains = json.load(f)

    corrected_stops = 0
    for tr in trains:
        for st in tr.get("stops", []):
            name = (st.get("station_name") or "").strip()
            curr_code = st.get("station_code", "").strip().upper()
            clean_name = re.sub(r"^\d+", "", name).strip().upper()

            for k, target_code in REFINED_NAME_MAP.items():
                if clean_name == k or clean_name.startswith(k):
                    if curr_code != target_code:
                        st["station_code"] = target_code
                        corrected_stops += 1
                    break

    print(f"Corrected {corrected_stops} stops to their canonical IRCTC codes!")

    # Save updated JSON
    with open(PRIMARY_PATH, "w", encoding="utf-8") as f:
        json.dump(trains, f, indent=2, ensure_ascii=False)
    print("Saved primary to:", PRIMARY_PATH)

    if SECONDARY_PATH.parent.exists():
        with open(SECONDARY_PATH, "w", encoding="utf-8") as f:
            json.dump(trains, f, indent=2, ensure_ascii=False)
        print("Saved secondary to:", SECONDARY_PATH)

    # Ingest into PostgreSQL
    sm = get_session_maker()
    async with sm() as session:
        print("\n--- PURGING OBSOLETE NARROW GAUGE STATIONS ---")
        await session.execute(text("DELETE FROM stations WHERE code IN ('JBPN', 'ITRN', 'NABN');"))
        await session.commit()
        print("Purged JBPN, ITRN, NABN from 'stations' table.")

        print("\n--- REPLACING TIMETABLE WITH CANONICAL STOPS ---")
        await session.execute(text("TRUNCATE TABLE timetable RESTART IDENTITY CASCADE;"))
        await session.commit()

        # Batch insert
        batch_size = 1000
        current_batch = []
        inserted = 0

        for tr in trains:
            t_num = tr["train_number"]
            t_name = tr["train_name"]

            for st in tr.get("stops", []):
                code = st.get("station_code", "").strip().upper()
                if not code:
                    continue

                arr_obj = parse_time_obj(st.get("arrival"))
                dep_obj = parse_time_obj(st.get("departure"))

                current_batch.append({
                    "train_number": t_num,
                    "train_name": t_name,
                    "station_code": code,
                    "station_name": st.get("station_name"),
                    "arrival": arr_obj,
                    "departure": dep_obj,
                    "day": st.get("day", 1),
                    "stop_sequence": st.get("stop_sequence", 1),
                })

                if len(current_batch) >= batch_size:
                    await session.execute(insert(TimetableModel).values(current_batch))
                    await session.commit()
                    inserted += len(current_batch)
                    current_batch = []

        if current_batch:
            await session.execute(insert(TimetableModel).values(current_batch))
            await session.commit()
            inserted += len(current_batch)

        print(f"Successfully re-ingested {inserted} timetable records with canonical station codes!")

if __name__ == "__main__":
    asyncio.run(apply_fixes())
