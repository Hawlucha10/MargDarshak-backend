import pdfplumber
from pathlib import Path

pdf_path = Path("D:/Sih58/NishkarshFoundData/Content/T/Table_56.pdf")
with pdfplumber.open(pdf_path) as pdf:
    for p_idx, page in enumerate(pdf.pages):
        table = page.extract_tables()[0]
        print(f"\n=======================================================")
        print(f"               PAGE {p_idx + 1} COLUMN MAPPING")
        print(f"=======================================================")
        print(f"Total Rows: {len(table)}, Total Cols: {len(table[0])}")
        
        # Print Row 0 (Train Numbers), Row 4 (Header), Row 9 (Gwalior), Row 28 (Jabalpur)
        for r_idx in [0, 1, 3, 4, 8, 9, 10, 20, 26, 28]:
            if r_idx < len(table):
                row = [str(c).replace('\n', ' ') if c is not None else '' for c in table[r_idx]]
                print(f"Row {r_idx:2d}:")
                for c_idx, val in enumerate(row):
                    print(f"   Col {c_idx:2d}: {val!r}")
