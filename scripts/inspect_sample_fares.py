import pypdf
import sys

sys.stdout.reconfigure(encoding='utf-8')
pdf_path = "D:/Sih58/NishkarshFoundData/Passengers Information/Fares.pdf"
reader = pypdf.PdfReader(pdf_path)

print("=== PAGE 8 (Mail/Express Sleeper) ===")
for l in reader.pages[7].extract_text().split("\n")[:25]:
    print(f"  {l.strip()}")

print("\n=== PAGE 11 (Mail/Express AC Classes) ===")
for l in reader.pages[10].extract_text().split("\n")[:25]:
    print(f"  {l.strip()}")

print("\n=== PAGE 61 (Other Charges / Surcharges) ===")
for l in reader.pages[60].extract_text().split("\n")[:25]:
    print(f"  {l.strip()}")
