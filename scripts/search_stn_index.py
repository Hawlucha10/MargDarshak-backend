import pypdf
from pathlib import Path

pdf_path = Path("D:/Sih58/NishkarshFoundData/Content/Station_Code_Index.pdf")
reader = pypdf.PdfReader(str(pdf_path))
all_text = ""
for p in reader.pages:
    all_text += p.extract_text() + "\n"

print("--- Searching for LKO or LUCKNOW ---")
for line in all_text.split("\n"):
    if "LKO" in line or "LUCKNOW" in line.upper() or "CSMT" in line or "MUMBAI" in line.upper() or "MADHOPUR" in line.upper():
        print(repr(line))
