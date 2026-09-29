import pdfplumber
from pathlib import Path

TABLES_DIR = Path("D:/Sih58/NishkarshFoundData/Content/T")

for t in ["28", "46", "49", "84"]:
    pdf_path = TABLES_DIR / f"Table_{t}.pdf"
    with pdfplumber.open(str(pdf_path)) as pdf:
        p0 = pdf.pages[0]
        words = p0.extract_words()
        print(f"\n--- TABLE {t} ---")
        # print words around top 100 to 200
        sample_words = [w for w in words if 100 <= w["top"] <= 200]
        for w in sorted(sample_words, key=lambda x: (x["top"], x["x0"]))[:20]:
            print(f"Top {w['top']:5.1f}, x0 {w['x0']:5.1f}, x1 {w['x1']:5.1f}: {w['text']}")
