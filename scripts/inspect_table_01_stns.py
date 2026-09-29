import pdfplumber
from pathlib import Path

pdf_path = Path("D:/Sih58/NishkarshFoundData/Content/T/Table_01.pdf")
with pdfplumber.open(str(pdf_path)) as pdf:
    p0 = pdf.pages[0]
    words = p0.extract_words()
    stn_words = [w for w in words if w["x1"] < 125 and w["top"] > 130]
    print(f"Total words in station/km region: {len(stn_words)}")
    
    # Group words by approximate vertical position (top)
    rows = {}
    for w in sorted(stn_words, key=lambda x: (x["top"], x["x0"])):
        # cluster within 3 points
        found_row = None
        for r_top in rows:
            if abs(w["top"] - r_top) < 3.5:
                found_row = r_top
                break
        if found_row is None:
            found_row = w["top"]
            rows[found_row] = []
        rows[found_row].append(w)

    for r_top in sorted(rows.keys()):
        row_words = rows[r_top]
        line = " ".join(w["text"] for w in row_words)
        print(f"Top {r_top:5.1f}: {line}")
