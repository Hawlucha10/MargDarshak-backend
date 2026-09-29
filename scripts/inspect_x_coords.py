import pdfplumber
import re
from pathlib import Path

pdf_path = Path("D:/Sih58/NishkarshFoundData/Content/T/Table_12.pdf")

with pdfplumber.open(str(pdf_path)) as pdf:
    p = pdf.pages[3] # page 4 (0-indexed 3)
    words = p.extract_words()
    
    # Let's find all words around the train number row (top between 100 and 150)
    train_row_words = [w for w in words if 110 <= w["top"] <= 135 and re.search(r"\d{5}", w["text"])]
    print(f"Train row words on Table 12, Page 4: {len(train_row_words)}")
    for w in sorted(train_row_words, key=lambda x: x["x0"]):
        print(f"  Train word: {w['text']:<12} x0={w['x0']:<6.1f} x1={w['x1']:<6.1f}")

    # Now let's find times at row 20 (Moradabad: 14.45, 00.28)
    # top between 300 and 350
    time_words = [w for w in words if 330 <= w["top"] <= 360 and re.search(r"\d{2}\.\d{2}", w["text"])]
    print(f"\nTime words around row 20 (Moradabad): {len(time_words)}")
    for w in sorted(time_words, key=lambda x: x["x0"]):
        print(f"  Time word: {w['text']:<10} x0={w['x0']:<6.1f} x1={w['x1']:<6.1f} top={w['top']:<6.1f}")
