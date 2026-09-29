import pdfplumber
import re
from pathlib import Path

pdf_path = Path("D:/Sih58/NishkarshFoundData/Content/T/Table_01.pdf")
with pdfplumber.open(str(pdf_path)) as pdf:
    p0 = pdf.pages[0]
    words = p0.extract_words()
    train_num_words = [w for w in words if re.match(r"^\d{5}", w["text"])]
    print("Found 5-digit train number words:", len(train_num_words))
    for w in sorted(train_num_words, key=lambda x: x["x0"]):
        print(f"Text: {w['text']:<10} x0={w['x0']:<6.1f} x1={w['x1']:<6.1f} top={w['top']:<6.1f} bottom={w['bottom']:<6.1f}")
