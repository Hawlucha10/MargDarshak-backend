import pypdf
from pathlib import Path

pdf_path = Path("D:/Sih58/NishkarshFoundData/Content/Station_Code_Index.pdf")
reader = pypdf.PdfReader(str(pdf_path))
all_lines = []
for p in reader.pages:
    for line in p.extract_text().split("\n"):
        all_lines.append(line.strip())

for idx, line in enumerate(all_lines):
    if any(k in line for k in ["CSMT", "LUCKNOW", "CHHATRAPATI", "MADHOPUR", "HOWRAH", "SECUNDERABAD"]):
        start = max(0, idx - 2)
        end = min(len(all_lines), idx + 3)
        print(f"Around index {idx}:")
        for i in range(start, end):
            print(f"  {i:3d}: {repr(all_lines[i])}")
        print("-" * 40)
