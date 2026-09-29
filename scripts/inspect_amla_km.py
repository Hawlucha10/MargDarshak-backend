import pdfplumber
from pathlib import Path

pdf_path = Path("D:/Sih58/NishkarshFoundData/Content/T/Table_02.pdf")
with pdfplumber.open(str(pdf_path)) as pdf:
    p = pdf.pages[0]
    words = [w for w in p.extract_words() if 370 <= w["top"] <= 430 and w["x1"] < 130]
    # sort by top, x0
    for w in sorted(words, key=lambda x: (x["top"], x["x0"])):
        print(f"Top {w['top']:5.1f}, x0 {w['x0']:5.1f}: {w['text']}")
