import pdfplumber
import re
from pathlib import Path

BASE_DIR = Path("D:/Sih58/NishkarshFoundData/Content/T")

# 1. Search all tables for 22182
found_in_tables = []
for p in sorted(BASE_DIR.glob("Table_*.pdf")):
    with pdfplumber.open(str(p)) as pdf:
        for p_idx, page in enumerate(pdf.pages):
            text = page.extract_text() or ""
            if "22182" in text:
                found_in_tables.append((p.name, p_idx + 1))

print(f"Train 22182 found in: {found_in_tables}")

# 2. Check Table 56 stations
t56_path = BASE_DIR / "Table_56.pdf"
with pdfplumber.open(str(t56_path)) as pdf:
    for page in pdf.pages:
        table = page.extract_tables()[0]
        # find col of 22182
        col_22182 = None
        for c in range(len(table[0])):
            if "22182" in str(table[0][c] or ""):
                col_22182 = c
                break
        print(f"Table 56 col for 22182: {col_22182}")
        if col_22182 is not None:
            for r in range(len(table)):
                stn = str(table[r][7] or table[r][6] or table[r][1] or "") # middle stn
                val = str(table[r][col_22182] or "").strip()
                all_cells = [str(c or "").strip() for c in table[r]]
                stn_name = ""
                for cell in all_cells:
                    if any(s in cell for s in ["Delhi", "Mathura", "Agra", "Gwalior", "Jhansi", "Lalitpur", "Bina", "Saugor", "Damoh", "Katni", "Jabalpur", "Malkhedi"]):
                        stn_name = cell.replace("\n", " ")
                if val:
                    print(f"  R{r:02d} [{stn_name}]: {repr(val)}")
