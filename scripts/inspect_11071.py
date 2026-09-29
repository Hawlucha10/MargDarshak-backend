import pdfplumber
from pathlib import Path

pdf_path = Path("D:/Sih58/NishkarshFoundData/Content/T/Table_06.pdf")
with pdfplumber.open(str(pdf_path)) as pdf:
    p = pdf.pages[0]
    words = p.extract_words()
    # words with 11071
    t_word = [w for w in words if "11071" in w["text"]][0]
    print("Train 11071:", t_word)
    # find words in this column (x between t_word[x0]-3 and t_word[x1]+3)
    col_words = [w for w in words if abs(w["x0"] - t_word["x0"]) < 6]
    for w in sorted(col_words, key=lambda x: x["top"]):
        if any(c.isdigit() for c in w["text"]):
            print(f"  top={w['top']:.1f}: {w['text']}")
