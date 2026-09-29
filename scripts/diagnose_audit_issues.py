"""
Diagnosis script to investigate the root causes identified in the audit.
"""

import json
import re
from pathlib import Path
import pdfplumber
import pypdf

BASE_DIR = Path("D:/Sih58/NishkarshFoundData")

def inspect_station_code_index():
    pdf_path = BASE_DIR / "Content" / "Station_Code_Index.pdf"
    print("=== INSPECTING Station_Code_Index.pdf ===")
    reader = pypdf.PdfReader(str(pdf_path))
    lines = []
    for p in reader.pages[:2]:
        for line in p.extract_text().split("\n"):
            line = line.strip()
            if line:
                lines.append(line)
    print(f"Total pages: {len(reader.pages)}")
    print("Sample lines from first 2 pages:")
    for l in lines[:25]:
        print(f"  {repr(l)}")

def inspect_table_garbled():
    print("\n=== INSPECTING GARBLED STATIONS ===")
    # Find which table contains 'V L Jh ir k s n n h s g m i an ib a i a'
    with open(BASE_DIR / "TAG_2026_complete_timetable.json", "r", encoding="utf-8") as f:
        trains = json.load(f)
    for t in trains:
        for s in t.get("stops", []):
            if "Jh ir" in s.get("station_name", "") or "Ti o la" in s.get("station_name", ""):
                print(f"Found garbled in Table_{t['table_number']}.pdf: Train {t['train_number']}, Name: {repr(s['station_name'])}")
                return t["table_number"]
    return None

def inspect_negative_halts():
    print("\n=== INSPECTING NEGATIVE HALTS (e.g. Table 06) ===")
    pdf_path = BASE_DIR / "Content" / "T" / "Table_06.pdf"
    with pdfplumber.open(str(pdf_path)) as pdf:
        table = pdf.pages[0].extract_tables()[0]
        # print first 15 rows of Table 06
        for r_idx in range(min(18, len(table))):
            row_str = [str(c or "")[:15].strip() for c in table[r_idx][:10]]
            print(f"R{r_idx:02d}: {row_str}")

if __name__ == "__main__":
    inspect_station_code_index()
    garbled_table = inspect_table_garbled()
    inspect_negative_halts()
