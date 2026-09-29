"""
Detailed inspection of Table_02.pdf and Table_06.pdf layouts and text.
"""

import pdfplumber
from pathlib import Path

BASE_DIR = Path("D:/Sih58/NishkarshFoundData/Content/T")

def examine(table_num):
    pdf_path = BASE_DIR / f"Table_{table_num:02d}.pdf"
    print(f"\n=================== TABLE {table_num:02d} ===================")
    with pdfplumber.open(str(pdf_path)) as pdf:
        p0 = pdf.pages[0]
        tables = p0.extract_tables()
        if not tables:
            print("No tables extracted!")
            return
        t = tables[0]
        print(f"Dimensions: {len(t)} rows x {len(t[0])} cols")
        print("\n--- Header Rows (0 to 6) ---")
        for r in range(min(7, len(t))):
            print(f"Row {r:02d}: {[repr(c) for c in t[r][:15]]}")

        print("\n--- Station Rows (sample 15 to 30) ---")
        for r in range(15, min(30, len(t))):
            print(f"Row {r:02d}: {[repr(c) for c in t[r][:12]]}")

examine(2)
examine(6)
examine(1)
examine(56)
