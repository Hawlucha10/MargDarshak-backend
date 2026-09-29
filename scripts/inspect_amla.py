import pdfplumber
from pathlib import Path

pdf_path = Path("D:/Sih58/NishkarshFoundData/Content/T/Table_02.pdf")
with pdfplumber.open(str(pdf_path)) as pdf:
    # check page 1 or 2
    for p_idx, p in enumerate(pdf.pages):
        words = p.extract_words()
        amla_words = [w for w in words if "Amla" in w["text"] or "Itarsi" in w["text"]]
        if amla_words:
            print(f"Table 02, Page {p_idx+1}:")
            for w in amla_words:
                print(f"  Word: {w['text']:<15} top={w['top']:.1f}, x0={w['x0']:.1f}")
