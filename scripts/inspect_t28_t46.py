import pdfplumber
from pathlib import Path

TABLES_DIR = Path("D:/Sih58/NishkarshFoundData/Content/T")

for t in ["28", "46"]:
    pdf_path = TABLES_DIR / f"Table_{t}.pdf"
    with pdfplumber.open(str(pdf_path)) as pdf:
        p0 = pdf.pages[0]
        words = p0.extract_words()
        print(f"\n=== TABLE {t} ===")
        # Look for station-like words or where Km is
        km_words = [w for w in words if "km" in w["text"].lower()]
        for w in km_words:
            print(f"  Km word: {w['text']} at x0={w['x0']:.1f}, top={w['top']:.1f}")
        # Look for train number row
        t_words = [w for w in words if "Train" in w["text"] or "TRAIN" in w["text"]]
        for w in t_words:
            print(f"  Header: {w['text']} at x0={w['x0']:.1f}, top={w['top']:.1f}")
