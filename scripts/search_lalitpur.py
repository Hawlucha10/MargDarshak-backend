import pypdf
from pathlib import Path

BASE_DIR = Path("D:/Sih58/NishkarshFoundData/Content/T")

print("=== SEARCHING FOR LALITPUR IN ALL 97 TABLES ===")
matches = []
for p in sorted(BASE_DIR.glob("Table_*.pdf")):
    try:
        reader = pypdf.PdfReader(str(p))
        for p_idx, page in enumerate(reader.pages):
            text = page.extract_text() or ""
            if "Lalitpur" in text or "LALITPUR" in text:
                matches.append((p.name, p_idx + 1))
    except Exception:
        pass

print(f"Lalitpur found in {len(matches)} places: {matches}")
