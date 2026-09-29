import pypdf
from pathlib import Path
import sys

# Ensure UTF-8 output
sys.stdout.reconfigure(encoding='utf-8')

pdf_path = Path("D:/Sih58/NishkarshFoundData/Passengers Information/Fares.pdf")
reader = pypdf.PdfReader(str(pdf_path))
print(f"Total pages in Fares.pdf: {len(reader.pages)}")

page_headings = []
for idx, p in enumerate(reader.pages):
    text = p.extract_text()
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    heading = lines[2] if len(lines) > 2 else (lines[0] if lines else "Empty")
    page_headings.append((idx + 1, heading))

for p_num, h in page_headings:
    if any(k in h.lower() for k in ["fare", "mail", "express", "rajdhani", "shatabdi", "superfast", "vande", "distance", "table"]):
        print(f"Page {p_num:2d}: {h}")
