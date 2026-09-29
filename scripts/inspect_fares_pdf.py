import pypdf
import pdfplumber
from pathlib import Path

pdf_path = Path("D:/Sih58/NishkarshFoundData/Passengers Information/Fares.pdf")
print("=== INSPECTING Fares.pdf ===")
reader = pypdf.PdfReader(str(pdf_path))
print(f"Total pages: {len(reader.pages)}")

for idx, p in enumerate(reader.pages):
    text = p.extract_text()
    print(f"\n--- PAGE {idx+1} ---")
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    for l in lines[:30]:
        print(f"  {l}")
