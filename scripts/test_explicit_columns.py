"""
Test explicit vertical columns in Table 06 and Table 12 with pdfplumber.
"""

import pdfplumber
import re
from pathlib import Path

BASE_DIR = Path("D:/Sih58/NishkarshFoundData/Content/T")

def test_explicit_columns(table_num):
    pdf_path = BASE_DIR / f"Table_{table_num:02d}.pdf"
    with pdfplumber.open(str(pdf_path)) as pdf:
        p = pdf.pages[0]
        words = p.extract_words()
        
        # Find train numbers
        train_words = [w for w in words if re.search(r"^\d{5}", w["text"]) and 100 <= w["top"] <= 140]
        train_words = sorted(train_words, key=lambda w: w["x0"])
        print(f"\nTable {table_num:02d}: Found {len(train_words)} trains in header")
        
        # Build vertical separators between trains
        v_lines = [0] # left edge
        # station column boundary: just before first train
        first_t_x = train_words[0]["x0"]
        v_lines.append(first_t_x - 3)
        
        for i in range(len(train_words) - 1):
            mid_x = (train_words[i]["x1"] + train_words[i+1]["x0"]) / 2.0
            v_lines.append(mid_x)
            
        v_lines.append(p.width)
        
        # Now extract table with explicit vertical lines!
        table_settings = {
            "vertical_strategy": "explicit",
            "explicit_vertical_lines": v_lines,
            "horizontal_strategy": "text",
            "intersection_x_tolerance": 3,
        }
        
        extracted = p.extract_table(table_settings)
        if extracted:
            print(f"Extracted dimensions: {len(extracted)} rows x {len(extracted[0])} cols")
            print(f"Header row (Train numbers): {extracted[1][1:]}")
            # check row 28 or sample station row
            for r in range(15, min(25, len(extracted))):
                stn_name = extracted[r][0].replace('\n', ' ') if extracted[r][0] else ""
                vals = [repr(c.replace('\n', ' ') if c else '') for c in extracted[r][1:5]]
                print(f"  R{r:02d} {stn_name[:18]:<18} | cols: {vals}")

test_explicit_columns(6)
test_explicit_columns(12)
