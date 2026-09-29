import pdfplumber
import re
from pathlib import Path

pdf_path = Path("D:/Sih58/NishkarshFoundData/Content/T/Table_12.pdf")

with pdfplumber.open(str(pdf_path)) as pdf:
    p = pdf.pages[3] # page 4
    words = p.extract_words()
    
    # Left margin words (x1 < 110)
    left_words = [w for w in words if w["x1"] < 110 and w["top"] > 140]
    
    # Group by vertical rows
    rows = []
    current_row = []
    current_top = -1
    for w in sorted(left_words, key=lambda x: (x["top"], x["x0"])):
        if current_top == -1 or abs(w["top"] - current_top) < 3.0:
            current_row.append(w)
            current_top = w["top"]
        else:
            rows.append((current_top, " ".join(x["text"] for x in current_row)))
            current_row = [w]
            current_top = w["top"]
    if current_row:
        rows.append((current_top, " ".join(x["text"] for x in current_row)))

    print(f"Total station rows on Table 12, Page 4: {len(rows)}")
    for top_y, text in rows[:35]:
        print(f"Top {top_y:5.1f}: {text}")
