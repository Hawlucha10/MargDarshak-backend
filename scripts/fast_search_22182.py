import pypdf
from pathlib import Path

BASE_DIR = Path("D:/Sih58/NishkarshFoundData/Content/T")

matches = []
for p in sorted(BASE_DIR.glob("Table_*.pdf")):
    try:
        reader = pypdf.PdfReader(str(p))
        for p_idx, page in enumerate(reader.pages):
            text = page.extract_text() or ""
            if "22182" in text:
                matches.append((p.name, p_idx + 1))
    except Exception as e:
        pass

print(f"Train 22182 found in {len(matches)} places: {matches}", flush=True)
