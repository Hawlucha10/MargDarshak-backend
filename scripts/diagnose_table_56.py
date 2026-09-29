import json
import pdfplumber
from pathlib import Path

# 1. Inspect Table_56_extracted_sample.json
json_path = Path("D:/Sih58/NishkarshFoundData/Table_56_extracted_sample.json")
with open(json_path, "r", encoding="utf-8") as f:
    trains = json.load(f)

print("=== JABALPUR IN JSON ===")
for t in trains[:8]:
    for s in t["stops"]:
        if "jabalpur" in s["station_name"].lower():
            print(f"Train {t['train_number']}: Name='{s['station_name']}', Code='{s['station_code']}', KM='{s['km']}', Arr={s['arrival']}, Dep={s['departure']}")

# 2. Inspect Raw PDF cells for Table 56 Page 1 & Page 2
pdf_path = Path("D:/Sih58/NishkarshFoundData/Content/T/Table_56.pdf")
with pdfplumber.open(pdf_path) as pdf:
    for p_idx in range(len(pdf.pages)):
        p = pdf.pages[p_idx]
        table = p.extract_tables()[0]
        print(f"\n=== PAGE {p_idx+1} ROWS 20 TO 29 (Cols 5 to 10) ===")
        for r in range(20, min(len(table), 30)):
            row = table[r]
            # Print col 5 (km?), col 6, col 7, col 8
            print(f"Row {r:2d}: {row[5:10]}")
