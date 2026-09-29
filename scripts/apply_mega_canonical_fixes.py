import asyncio
import json
import os
from sqlalchemy import text
from app.db.postgres import get_session_maker

# 12 Missing Modern / Renamed Stations with PostGIS coordinates
NEW_STATIONS = [
    {"code": "NDPM", "name": "NARMADAPURAM", "state": "Madhya Pradesh", "zone": "WCR", "lat": 22.7519, "lon": 77.7289},
    {"code": "PCOI", "name": "PRAYAGRAJ CHHEOKI", "state": "Uttar Pradesh", "zone": "NCR", "lat": 25.3855, "lon": 81.8794},
    {"code": "MCTM", "name": "MCTM UDHAMPUR", "state": "Jammu and Kashmir", "zone": "NR", "lat": 32.9150, "lon": 75.0080},
    {"code": "MBDP", "name": "MAA BELHA DEVI DHAM PRATAPGARH", "state": "Uttar Pradesh", "zone": "NR", "lat": 25.9030, "lon": 81.9890},
    {"code": "SMVJ", "name": "SHRI MAHAVEERJI", "state": "Rajasthan", "zone": "WCR", "lat": 26.8524, "lon": 76.9942},
    {"code": "SHRN", "name": "SANT HIRDARAM NAGAR", "state": "Madhya Pradesh", "zone": "WCR", "lat": 23.2750, "lon": 77.3400},
    {"code": "YNRK", "name": "YOG NAGARI RISHIKESH", "state": "Uttarakhand", "zone": "NR", "lat": 30.0930, "lon": 78.2770},
    {"code": "EKNR", "name": "EKTA NAGAR", "state": "Gujarat", "zone": "WR", "lat": 21.8700, "lon": 73.6900},
    {"code": "KRMR", "name": "KARIMNAGAR", "state": "Telangana", "zone": "SCR", "lat": 18.4386, "lon": 79.1288},
    {"code": "SINA", "name": "SRINAGAR KASHMIR", "state": "Jammu and Kashmir", "zone": "NR", "lat": 33.9960, "lon": 74.8360},
    {"code": "DADN", "name": "DR AMBEDKAR NAGAR", "state": "Madhya Pradesh", "zone": "WR", "lat": 22.5510, "lon": 75.7610},
    {"code": "ROJ",  "name": "RANINAGAR JALPAIGURI", "state": "West Bengal", "zone": "NFR", "lat": 26.5400, "lon": 88.7200},
]

# Canonical Station Replacement Rules:
# (old_code, substring_in_name_lower) -> (new_code, new_name)
CANONICAL_RULES = [
    # Mangaluru
    ("MANG", "mangaluru jn", "MAJN", "Mangaluru Jn."),
    ("MANG", "mangaluru central", "MAQ", "Mangaluru Central"),
    ("MANG", "mangaluru", "MAJN", "Mangaluru Jn."),
    
    # Hubballi
    ("BLLI", "hubballi", "UBL", "SSS Hubballi"),
    
    # Mayiladuthurai
    ("ADT", "aduturai", "MV", "Mayiladuturai Jn."),
    ("ADT", "yiladuturai", "MV", "Mayiladuturai Jn."),
    
    # Narmadapuram
    ("ADX", "narmadapuram", "NDPM", "Narmadapuram"),
    
    # Sewagram & Prayagraj
    ("AGC", "sewagram", "SEGM", "Sewagram"),
    ("AGC", "paryagraj chheoki", "PCOI", "Prayagraj Chheoki"),
    ("AGC", "paryagraj", "PRYJ", "Prayagraj"),
    ("AGC", "rayagraj", "PRYJ", "Prayagraj"),
    ("AGC", "nagrakata", "NKB", "Nagrakata"),
    
    # Banaras
    ("ANR", "banaras", "BSBS", "Banaras"),
    
    # Udhampur
    ("APTA", "tushar mahajan", "MCTM", "MCTM Udhampur"),
    
    # Bettiah
    ("BETI", "betiah", "BTH", "Bettiah"),
    
    # Ambala Cantt
    ("BLRD", "mbala cantt", "UMB", "Ambala Cantt."),
    
    # Pratapgarh
    ("BYL", "belha devi", "MBDP", "Maa Belha Devi Dham Pratapgarh"),
    
    # Visakhapatnam
    ("HAPA", "khapatnam", "VSKP", "Visakhapatnam"),
    
    # Guwahati
    ("HATI", "guwahati", "GHY", "Guwahati"),
    ("HATI", "ahati", "GHY", "Guwahati"),
    
    # Kochuveli / Trivandrum
    ("HPU", "thiruvanthapuram north", "KCVL", "Kochuveli (TVM North)"),
    ("HPU", "hiruvanthapuram north", "KCVL", "Kochuveli (TVM North)"),
    ("HPU", "thiruvananthapur", "TVC", "Thiruvananthapuram Central"),
    ("HPU", "uvananthapuram", "TVC", "Thiruvananthapuram Central"),
    ("HPU", "chapurmukh", "CPK", "Chaparmukh Jn."),
    
    # Indore
    ("INDM", "ndore", "INDB", "Indore Jn."),
    
    # Vaishno Devi Katra
    ("KEA", "vaishno devi", "SVDK", "Shri Mata Vaishno Devi Katra"),
    ("KEA", "vaishn devi", "SVDK", "Shri Mata Vaishno Devi Katra"),
    
    # Sirpur Kaghaznagar
    ("KGA", "khagaznagar", "SKZR", "Sirpur Kaghaznagar"),
    
    # Kurnool City
    ("KURN", "kurnool", "KRNT", "Kurnool City"),
    
    # Samakhiali
    ("MKHI", "samakhiyali", "SIOB", "Samakhiali Jn."),
    
    # Rajnandgaon
    ("NGN", "rajnandgaon", "RJN", "Rajnandgaon"),
    
    # Kopergaon
    ("PG", "kopergaon", "KPG", "Kopergaon"),
    
    # SMVT Bengaluru
    ("RAYA", "vishvesvaraya", "SMVB", "SMVT Bengaluru"),
    ("RAYA", "visvesvaraya", "SMVB", "SMVT Bengaluru"),
    ("RAYA", "vishveswaraya", "SMVB", "SMVT Bengaluru"),
    
    # Shivamogga Town
    ("SHIV", "shivamogga", "SMET", "Shivamogga Town"),
    
    # Pathankot Cantt
    ("THAN", "pathan kot cantt", "PTKC", "Pathankot Cantt"),
    
    # Shri Mahaveerji
    ("VEER", "mahaveerji", "SMVJ", "Shri Mahaveerji"),
    
    # Kurduwadi & Banaswadi
    ("WADI", "kurduwadi", "KWV", "Kurduwadi"),
    ("WADI", "naswadi", "BAND", "Banaswadi"),
    
    # NGE (Nagar misparses)
    ("NGE", "sambhaji nagar", "AWB", "Chhatrapati Sambhaji Nagar (Aurangabad)"),
    ("NGE", "ahilyanagar", "ANG", "Ahilyanagar (Ahmednagar)"),
    ("NGE", "ahaliyanagar", "ANG", "Ahilyanagar (Ahmednagar)"),
    ("NGE", "ahmednagar", "ANG", "Ahilyanagar (Ahmednagar)"),
    ("NGE", "surendra nagar", "SUNR", "Surendranagar"),
    ("NGE", "urendranagar", "SUNR", "Surendranagar"),
    ("NGE", "sri ganga nagar", "SGNR", "Sri Ganganagar"),
    ("NGE", "sriganganagar", "SGNR", "Sri Ganganagar"),
    ("NGE", "sai nagar shirdi", "SNSI", "Sainagar Shirdi"),
    ("NGE", "mahabubnagar", "MBNR", "Mahabubnagar"),
    ("NGE", "zianagaram", "VZM", "Vizianagaram"),
    ("NGE", "nagaram", "VZM", "Vizianagaram"),
    ("NGE", "sant hirdaram nagar", "SHRN", "Sant Hirdaram Nagar"),
    ("NGE", "sirpur kagaz nagar", "SKZR", "Sirpur Kaghaznagar"),
    ("NGE", "gomtinagar", "GTNR", "Gomtinagar (Lucknow)"),
    ("NGE", "rajendranagar", "RJPB", "Rajendra Nagar (T) Patna"),
    ("NGE", "rajendra nagar", "RJPB", "Rajendra Nagar (T) Patna"),
    ("NGE", "rajen- dranagar", "RJPB", "Rajendra Nagar (T) Patna"),
    ("NGE", "virdunagar", "VPT", "Virudhunagar Jn."),
    ("NGE", "udunagar", "VPT", "Virudhunagar Jn."),
    ("NGE", "tatanagar", "TATA", "Tatanagar"),
    ("NGE", "atanagar", "TATA", "Tatanagar"),
    ("NGE", "tanagar", "TATA", "Tatanagar"),
    ("NGE", "rishikes", "YNRK", "Yog Nagari Rishikesh"),
    ("NGE", "ekta nagar", "EKNR", "Ekta Nagar"),
    ("NGE", "ektanagar", "EKNR", "Ekta Nagar"),
    ("NGE", "kta nagar", "EKNR", "Ekta Nagar"),
    ("NGE", "karimnagar", "KRMR", "Karimnagar"),
    ("NGE", "shaktinagar", "SKTN", "Shaktinagar"),
    ("NGE", "sri nagar", "SINA", "Srinagar"),
    ("NGE", "ambedkar nagar", "DADN", "Dr. Ambedkar Nagar"),
    ("NGE", "raninagar", "ROJ", "Raninagar Jalpaiguri"),
    ("NGE", "himmat nagar", "HMT", "Himmatnagar"),
]

async def apply_repairs():
    sm = get_session_maker()
    async with sm() as db:
        print("--- Step 1: Inserting missing modern/renamed stations into stations table ---")
        for stn in NEW_STATIONS:
            q = text("""
                INSERT INTO stations (code, name, state, zone, lat, lon, geom)
                VALUES (:code, :name, :state, :zone, CAST(:lat AS numeric), CAST(:lon AS numeric), 
                        ST_SetSRID(ST_MakePoint(CAST(:lon AS double precision), CAST(:lat AS double precision)), 4326))
                ON CONFLICT (code) DO UPDATE
                SET name = EXCLUDED.name, state = EXCLUDED.state, zone = EXCLUDED.zone,
                    lat = EXCLUDED.lat, lon = EXCLUDED.lon, geom = EXCLUDED.geom;
            """)
            await db.execute(q, stn)
        await db.commit()
        print(f"Successfully ensured {len(NEW_STATIONS)} stations exist in PostgreSQL stations table.")

        print("\n--- Step 2: Applying Canonical Fixes to PostgreSQL timetable ---")
        total_updated = 0
        for old_code, sub_name, new_code, new_name in CANONICAL_RULES:
            q_update = text("""
                UPDATE timetable
                SET station_code = :new_code,
                    station_name = :new_name
                WHERE station_code = :old_code
                  AND lower(coalesce(station_name, '')) LIKE '%' || :sub_name || '%'
            """)
            res = await db.execute(q_update, {
                "old_code": old_code,
                "sub_name": sub_name,
                "new_code": new_code,
                "new_name": new_name
            })
            if res.rowcount > 0:
                print(f"Fixed {res.rowcount:3d} stops: [{old_code}] '{sub_name}' -> [{new_code}] {new_name}")
                total_updated += res.rowcount
        await db.commit()
        print(f"\nTotal timetable stops canonically corrected in PostgreSQL: {total_updated}")

        # Also purge any remaining obsolete narrow gauge stations from stations
        await db.execute(text("DELETE FROM stations WHERE code IN ('JBPN', 'ITRN', 'NABN')"))
        await db.commit()
        print("Purged obsolete narrow gauge stations.")

def repair_json_files():
    print("\n--- Step 3: Mirroring fixes to Timetable JSON files ---")
    json_paths = [
        r"D:\Sih58\NishkarshFoundData\TAG_2026_complete_timetable.json",
        r"d:\Yue\Ura\Sih 58\NishkarshFoundData\TAG_2026_complete_timetable.json",
    ]

    for path in json_paths:
        if not os.path.exists(path):
            print(f"File not found: {path}")
            continue
        print(f"Processing JSON: {path}")
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        updated_count = 0
        for train in data:
            for stop in train.get("stops", []):
                old_code = stop.get("station_code", "").upper().strip()
                name_lower = stop.get("station_name", "").lower()
                for rule_old, sub_name, new_code, new_name in CANONICAL_RULES:
                    if old_code == rule_old and sub_name in name_lower:
                        stop["station_code"] = new_code
                        stop["station_name"] = new_name
                        updated_count += 1
                        break

        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"Updated {updated_count} stops in {path}")

if __name__ == "__main__":
    asyncio.run(apply_repairs())
    repair_json_files()
    print("\nAll canonical station fixes successfully applied!")
