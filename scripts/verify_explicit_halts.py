"""
Verification of explicit vertical lines on Table 06 and Table 12.
"""

import pdfplumber
import re
from pathlib import Path

BASE_DIR = Path("D:/Sih58/NishkarshFoundData/Content/T")

def parse_with_explicit_lines(table_num):
    pdf_path = BASE_DIR / f"Table_{table_num:02d}.pdf"
    with pdfplumber.open(str(pdf_path)) as pdf:
        p = pdf.pages[0]
        words = p.extract_words()
        
        # 1. Train words
        train_words = [w for w in words if re.search(r"^\d{5}", w["text"]) and 100 <= w["top"] <= 150]
        train_words = sorted(train_words, key=lambda w: w["x0"])
        
        # 2. Leftmost train determines station right bound
        first_t_x = train_words[0]["x0"]
        
        # 3. Explicit vertical lines:
        # Col 0: KM / Station column: [0, first_t_x - 3]
        # Then dividing line between each train
        v_lines = [0, first_t_x - 3]
        for i in range(len(train_words) - 1):
            mid_x = (train_words[i]["x1"] + train_words[i+1]["x0"]) / 2.0
            v_lines.append(mid_x)
        v_lines.append(p.width)
        
        table = p.extract_table({
            "vertical_strategy": "explicit",
            "explicit_vertical_lines": v_lines,
            "horizontal_strategy": "text",
        })
        
        print(f"\nTable {table_num:02d}: Extracted {len(table)} rows x {len(table[0])} cols")
        # Column 0 is station column
        # Columns 1..N are train columns
        train_nums = [re.search(r"\d{5}", tw["text"]).group(0) for tw in train_words]
        print(f"Train numbers ({len(train_nums)}): {train_nums}")
        
        # Check halts for all trains in this table
        neg_halts = 0
        for col_idx in range(1, len(table[0])):
            t_num = train_nums[col_idx - 1] if col_idx - 1 < len(train_nums) else f"Col{col_idx}"
            # find arrival and departure pairs
            r = 0
            while r < len(table):
                cell_val = str(table[r][col_idx] or "").strip()
                stn_name = str(table[r][0] or "").replace("\n", " ").strip()
                # If station has 'a' and next has 'd':
                m_time = re.findall(r"\b\d{1,2}[.:]\d{2}\b", cell_val)
                if m_time and r + 1 < len(table):
                    next_cell = str(table[r+1][col_idx] or "").strip()
                    m_next = re.findall(r"\b\d{1,2}[.:]\d{2}\b", next_cell)
                    if m_next:
                        arr_s = m_time[0].replace(".", ":")
                        dep_s = m_next[0].replace(".", ":")
                        a_h, a_m = map(int, arr_s.split(":"))
                        d_h, d_m = map(int, dep_s.split(":"))
                        if d_h * 60 + d_m < a_h * 60 + a_m:
                            neg_halts += 1
                            print(f"  [NEG] {t_num} at {stn_name}: Arr {arr_s} > Dep {dep_s}")
                        r += 1 # skip next
                r += 1
        print(f"Table {table_num:02d}: Total Negative Halts = {neg_halts}")

parse_with_explicit_lines(6)
parse_with_explicit_lines(12)
