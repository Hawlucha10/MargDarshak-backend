"""
Clean and Standardize Timetable + Enrich Commercial Halts
=========================================================
1. Removes empty/stray digit station codes (phantom header rows).
2. Maps all 4-letter / abbreviated station headers to canonical IRCTC station codes.
3. Enriches Train 22182 (NZM -> JBP) and 22181 (JBP -> NZM) with all intermediate commercial halts:
   - Lalitpur (LAR)
   - Bina Malkhedi (MAKR)
   - Khurai (KYE)
   - Patharia (PHA)
   - Bandakpur (BNU)
   - Sihora Road (SHR)
4. Saves polished timetable to both repository paths.
"""

import json
from pathlib import Path

SOURCE_PATH = Path("D:/Sih58/NishkarshFoundData/TAG_2026_complete_timetable.json")
BACKUP_PATH = Path("D:/Sih58/NishkarshFoundData/TAG_2026_complete_timetable.bak.json")
SECONDARY_PATH = Path("d:/Yue/Ura/Sih 58/NishkarshFoundData/TAG_2026_complete_timetable.json")

# Mapping of PDF header truncated / alternative codes to official IRCTC codes
CODE_NORMALIZATION = {
    # Delhi & North
    "HNZM": "NZM",
    "HNIZ": "NZM",
    "JMMU": "JAT",
    "JAMM": "JAT",
    "REAS": "REASI",
    "HISS": "HSR",
    "NAGA": "NLDM",
    "KOTK": "KKP",
    "BAGH": "BPM",
    "LALK": "LKU",

    # Central & MP
    "SAGO": "SGO",
    "VGLB": "VGLJ",
    "JHS": "VGLJ",
    "USLA": "USL",
    "NARS": "NU",
    "AMAR": "AMI",
    "SCBO": "GMO",

    # Mumbai & Maharashtra
    "MUMB": "CSMT",
    "UMBA": "CSMT",
    "LOKM": "LTT",
    "OKMA": "LTT",
    "LONA": "LNL",
    "CHHA": "KOP",
    "SHRI": "KOP",
    "ARDH": "WR",
    "ANDR": "BDTS",

    # South
    "KSRB": "SBC",
    "BENG": "BNC",
    "SIRM": "SMVB",
    "SMVT": "SMVB",
    "HAZU": "NED",
    "TUMA": "TK",
    "MYSU": "MYS",
    "KALA": "KLBG",
    "VIJA": "BJP",
    "HOSA": "HPT",
    "BALL": "BAY",
    "DAVA": "DVG",
    "ALNA": "LWR",
    "NELA": "NMGA",
    "CHIK": "CMGR",
    "SRIS": "SSPN",
    "SIND": "SNDR",
    "CHER": "CHZ",
    "MAHA": "MABD",
    "MIRY": "MRGA",
    "SATT": "SAP",
    "NADI": "NDKD",
    "ALAP": "ALLP",
    "LAPP": "ALLP",
    "KOCH": "KCVL",
    "OLLA": "QLN",
    "HORA": "SRR",
    "KANN": "CAPE",
    "VRID": "VRI",
    "VANC": "MEJ",
    "NCHI": "MEJ",
    "KODA": "KQN",
    "NAMA": "NMKL",
    "MAKK": "NMKL",
    "LEMJ": "SA",
    "RURJ": "KRR",
    "MGRC": "MAS",
    "DURA": "MDU",
    "GERC": "NCJ",
    "ERCO": "NCJ",
    "RCOI": "NCJ",
    "ODEJ": "ED",
    "UPPU": "TUP",
    "IMBA": "CBE",
    "UCHC": "TPJ",
    "ANJA": "TJ",
    "CUDD": "HX",
    "BELL": "BPA",
    "VASC": "VSG",
    "ASCO": "VSG",
    "CANA": "CNO",
    "URAT": "SL",

    # East & North East
    "NEWA": "NOQ",
    "NEWB": "NBQ",
    "ALIP": "APDJ",
    "ALLI": "APDJ",
    "NEWH": "NHLG",
    "HAMI": "HOJ",
    "COOC": "COB",
    "DALG": "DLO",
    "NABA": "NDAE",
    "MIDN": "MDN",
    "IDNA": "MDN",
    "AMPU": "RPH",
    "BERH": "BPC",
    "PURN": "PRNA",
    "SAIR": "SIHM",
    "OKAR": "BKSC",
    "ZARI": "HZBN",
    "MOKA": "MKA",
    "OKAM": "MKA",
    "SISW": "SBZ",
    "SHAA": "SPP",
    "SONE": "SEE",
    "MUZA": "MFP",
    "RUSE": "ROA",
    "EHRI": "DOS",

    # UP & North Central
    "PTDE": "DDU",
    "EORI": "DEOS",
    "AISH": "ASH",
    "ITAP": "STP",
    "GHAZ": "GCT",
    "NURI": "ARJ",
    "ANUR": "ARJ",
    "ATEH": "FTP",
    "AWAH": "ETW",
    "HIKO": "SKB",
    "UNDL": "TDL",
    "IGAR": "ALJN",
    "HURJ": "KRJ",
    "HAZI": "GZB",
    "KANA": "KJN",
    "RAEB": "RBL",
    "KANP": "CPA",
    "ANPU": "CPA",

    # West (Rajasthan / Gujarat)
    "RING": "RGS",
    "SAMD": "SMR",
    "CHAN": "CNA",
    "SAWA": "SWM",
    "AWAI": "SWM",
    "INDE": "IDG",
    "DHRA": "DHG",
    "SUJA": "SUJH",
    "VIRA": "VG",
    "UDNA": "UDN",
    "PORB": "PBR",
}

# 22182 Full Schedule (NZM -> JBP)
FULL_STOPS_22182 = [
    {"stop_sequence": 1, "station_code": "NZM", "station_name": "Hazrat Nizamuddin", "arrival": None, "departure": "17:45:00", "day": 1, "distance_km": 0},
    {"stop_sequence": 2, "station_code": "MTJ", "station_name": "Mathura Junction", "arrival": "19:03:00", "departure": "19:05:00", "day": 1, "distance_km": 134},
    {"stop_sequence": 3, "station_code": "AGC", "station_name": "Agra Cantt", "arrival": "19:48:00", "departure": "19:50:00", "day": 1, "distance_km": 188},
    {"stop_sequence": 4, "station_code": "GWL", "station_name": "Gwalior Junction", "arrival": "21:30:00", "departure": "21:32:00", "day": 1, "distance_km": 306},
    {"stop_sequence": 5, "station_code": "VGLJ", "station_name": "Virangana Lakshmibai Jhansi", "arrival": "23:10:00", "departure": "23:18:00", "day": 1, "distance_km": 403},
    {"stop_sequence": 6, "station_code": "LAR", "station_name": "Lalitpur Junction", "arrival": "00:13:00", "departure": "00:15:00", "day": 2, "distance_km": 494},
    {"stop_sequence": 7, "station_code": "MAKR", "station_name": "Bina Malkhedi Junction", "arrival": "01:43:00", "departure": "01:45:00", "day": 2, "distance_km": 557},
    {"stop_sequence": 8, "station_code": "KYE", "station_name": "Khurai", "arrival": "02:03:00", "departure": "02:05:00", "day": 2, "distance_km": 574},
    {"stop_sequence": 9, "station_code": "SGO", "station_name": "Saugor", "arrival": "02:30:00", "departure": "02:35:00", "day": 2, "distance_km": 627},
    {"stop_sequence": 10, "station_code": "PHA", "station_name": "Patharia", "arrival": "03:13:00", "departure": "03:15:00", "day": 2, "distance_km": 678},
    {"stop_sequence": 11, "station_code": "DMO", "station_name": "Damoh", "arrival": "03:40:00", "departure": "03:45:00", "day": 2, "distance_km": 704},
    {"stop_sequence": 12, "station_code": "BNU", "station_name": "Bandakpur", "arrival": "04:03:00", "departure": "04:05:00", "day": 2, "distance_km": 720},
    {"stop_sequence": 13, "station_code": "KMZ", "station_name": "Katni Murwara", "arrival": "05:05:00", "departure": "05:10:00", "day": 2, "distance_km": 813},
    {"stop_sequence": 14, "station_code": "SHR", "station_name": "Sihora Road", "arrival": "06:18:00", "departure": "06:20:00", "day": 2, "distance_km": 866},
    {"stop_sequence": 15, "station_code": "JBP", "station_name": "Jabalpur", "arrival": "07:25:00", "departure": None, "day": 2, "distance_km": 906},
]

# 22181 Full Schedule (JBP -> NZM)
FULL_STOPS_22181 = [
    {"stop_sequence": 1, "station_code": "JBP", "station_name": "Jabalpur", "arrival": None, "departure": "15:15:00", "day": 1, "distance_km": 0},
    {"stop_sequence": 2, "station_code": "SHR", "station_name": "Sihora Road", "arrival": "15:43:00", "departure": "15:45:00", "day": 1, "distance_km": 40},
    {"stop_sequence": 3, "station_code": "KMZ", "station_name": "Katni Murwara", "arrival": "16:35:00", "departure": "16:40:00", "day": 1, "distance_km": 93},
    {"stop_sequence": 4, "station_code": "BNU", "station_name": "Bandakpur", "arrival": "17:33:00", "departure": "17:35:00", "day": 1, "distance_km": 186},
    {"stop_sequence": 5, "station_code": "DMO", "station_name": "Damoh", "arrival": "18:00:00", "departure": "18:05:00", "day": 1, "distance_km": 202},
    {"stop_sequence": 6, "station_code": "PHA", "station_name": "Patharia", "arrival": "18:28:00", "departure": "18:30:00", "day": 1, "distance_km": 228},
    {"stop_sequence": 7, "station_code": "SGO", "station_name": "Saugor", "arrival": "19:25:00", "departure": "19:30:00", "day": 1, "distance_km": 279},
    {"stop_sequence": 8, "station_code": "KYE", "station_name": "Khurai", "arrival": "20:13:00", "departure": "20:15:00", "day": 1, "distance_km": 332},
    {"stop_sequence": 9, "station_code": "MAKR", "station_name": "Bina Malkhedi Junction", "arrival": "20:38:00", "departure": "20:40:00", "day": 1, "distance_km": 349},
    {"stop_sequence": 10, "station_code": "LAR", "station_name": "Lalitpur Junction", "arrival": "21:28:00", "departure": "21:30:00", "day": 1, "distance_km": 412},
    {"stop_sequence": 11, "station_code": "VGLJ", "station_name": "Virangana Lakshmibai Jhansi", "arrival": "22:35:00", "departure": "22:43:00", "day": 1, "distance_km": 503},
    {"stop_sequence": 12, "station_code": "GWL", "station_name": "Gwalior Junction", "arrival": "23:43:00", "departure": "23:45:00", "day": 1, "distance_km": 600},
    {"stop_sequence": 13, "station_code": "AGC", "station_name": "Agra Cantt", "arrival": "01:25:00", "departure": "01:27:00", "day": 2, "distance_km": 718},
    {"stop_sequence": 14, "station_code": "MTJ", "station_name": "Mathura Junction", "arrival": "02:02:00", "departure": "02:04:00", "day": 2, "distance_km": 772},
    {"stop_sequence": 15, "station_code": "NZM", "station_name": "Hazrat Nizamuddin", "arrival": "04:10:00", "departure": None, "day": 2, "distance_km": 906},
]

def clean_and_enrich():
    print("Loading timetable...")
    with open(SOURCE_PATH, "r", encoding="utf-8") as f:
        trains = json.load(f)
    print(f"Loaded {len(trains)} trains.")

    # Create backup
    with open(BACKUP_PATH, "w", encoding="utf-8") as f:
        json.dump(trains, f, indent=2)
    print("Backup created at:", BACKUP_PATH)

    cleaned_trains = []
    total_stops_before = 0
    total_stops_after = 0
    standardized_count = 0
    removed_empty_count = 0

    for tr in trains:
        t_num = tr["train_number"]
        
        # Override 22182 and 22181 with complete commercial stops
        if t_num == "22182":
            tr["stops"] = FULL_STOPS_22182
            tr["train_name"] = "NZM JBP Gondwana Express"
            cleaned_trains.append(tr)
            total_stops_after += len(FULL_STOPS_22182)
            continue
        elif t_num == "22181":
            tr["stops"] = FULL_STOPS_22181
            tr["train_name"] = "JBP NZM Gondwana Express"
            cleaned_trains.append(tr)
            total_stops_after += len(FULL_STOPS_22181)
            continue

        new_stops = []
        for s in tr.get("stops", []):
            total_stops_before += 1
            raw_code = s.get("station_code", "").strip().upper()
            raw_name = s.get("station_name", "") or ""

            # Check if code is empty or numeric phantom
            if not raw_code or raw_code.isdigit() or len(raw_code) < 2:
                removed_empty_count += 1
                continue

            # Contextual resolution for ambiguous codes
            code = raw_code
            if code == "RAJA":
                code = "RKM" if "mandi" in raw_name.lower() else "RJY"
            elif code == "TIRU":
                code = "TPJ" if "tiruch" in raw_name.lower() else ("TDPR" if "tiruppad" in raw_name.lower() else "TPTY")
            elif code == "DHAR":
                code = "DWR" if "dharwad" in raw_name.lower() else ("UMD" if "dharashiv" in raw_name.lower() else "DMR")
            elif code in CODE_NORMALIZATION:
                code = CODE_NORMALIZATION[code]
                standardized_count += 1

            s["station_code"] = code
            new_stops.append(s)

        # Re-sequence stops sequentially starting from 1
        for idx, st in enumerate(new_stops):
            st["stop_sequence"] = idx + 1

        tr["stops"] = new_stops
        total_stops_after += len(new_stops)
        cleaned_trains.append(tr)

    print("\n--- CLEANING & ENRICHMENT REPORT ---")
    print(f"Total Trains: {len(cleaned_trains)}")
    print(f"Total Stops Before: {total_stops_before}")
    print(f"Removed Phantom / Empty Stops: {removed_empty_count}")
    print(f"Standardized Truncated Station Codes: {standardized_count}")
    print(f"Total Stops After: {total_stops_after}")

    # Save to primary path
    with open(SOURCE_PATH, "w", encoding="utf-8") as f:
        json.dump(cleaned_trains, f, indent=2, ensure_ascii=False)
    print("Saved primary to:", SOURCE_PATH)

    # Save to secondary path
    if SECONDARY_PATH.parent.exists():
        with open(SECONDARY_PATH, "w", encoding="utf-8") as f:
            json.dump(cleaned_trains, f, indent=2, ensure_ascii=False)
        print("Saved secondary to:", SECONDARY_PATH)

if __name__ == "__main__":
    clean_and_enrich()
