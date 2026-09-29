"""
Parse official TAG 2026 Reference Indexes:
1. Station_Code_Index.pdf (Station Name -> Station Code)
2. Trains_Number_Index.pdf (Train Number -> Name, Origin, Destination, Tables)
"""

import re
import json
from pathlib import Path
import pypdf

STN_PDF = Path("D:/Sih58/NishkarshFoundData/Content/Station_Code_Index.pdf")
TRAIN_PDF = Path("D:/Sih58/NishkarshFoundData/Content/Trains_Number_Index.pdf")


def parse_station_code_index():
    reader = pypdf.PdfReader(str(STN_PDF))
    stn_map = {}
    for p in reader.pages:
        text = p.extract_text()
        for line in text.split("\n"):
            line = line.strip()
            # Matches: "BAKTHIYARPUR BKP", "KSR BENGALURU SBC", "BANDRA (T) BDTS"
            m = re.match(r"^(.*?)\s+([A-Z]{2,6})$", line)
            if m:
                name, code = m.group(1).strip(), m.group(2).strip()
                if len(name) > 1 and not name.startswith("TAG-") and name != "Station Name":
                    stn_map[name.upper()] = code
    return stn_map


def parse_train_number_index():
    reader = pypdf.PdfReader(str(TRAIN_PDF))
    trains_map = {}
    pattern = re.compile(r"(\d{5})(?:/(\d{5}))?\s+(.*?)\s+(TOD Exp|Exp|Express|Mail|SF|Shatabdi|Rajdhani|Pass|Spl|Special)")
    
    for p_idx, p in enumerate(reader.pages):
        text = p.extract_text()
        for line in text.split("\n"):
            line = line.strip()
            m = re.search(r"(\d{5})(?:/(\d{5}))?\s+(.+)", line)
            if m:
                t1 = m.group(1)
                t2 = m.group(2)
                rest = m.group(3).strip()
                trains_map[t1] = rest
                if t2:
                    trains_map[t2] = rest

    return trains_map


def main():
    stn_dict = parse_station_code_index()
    train_dict = parse_train_number_index()

    print(f"Parsed {len(stn_dict)} stations from Station_Code_Index.pdf")
    print(f"Parsed {len(train_dict)} trains from Trains_Number_Index.pdf")

    print("\n--- SAMPLE STATIONS ---")
    for sample in ["GWALIOR", "KSR BENGALURU", "NEW DELHI", "CHHATARPUR", "KHAJURAHO", "AYODHYA", "PRAYAGRAJ", "RANI KAMALAPATI"]:
        matches = [(k, v) for k, v in stn_dict.items() if sample in k]
        print(f"  Query '{sample}': {matches}")

    print("\n--- SAMPLE TRAINS ---")
    for tn in ["12627", "12780", "22470", "22469", "12156", "12002", "20802"]:
        print(f"  Train {tn}: {train_dict.get(tn, 'Not in index')}")


if __name__ == "__main__":
    main()
