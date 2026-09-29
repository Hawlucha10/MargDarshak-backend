import pdfplumber
import re
from pathlib import Path

TABLES_DIR = Path("D:/Sih58/NishkarshFoundData/Content/T")

pdf_files = sorted(list(TABLES_DIR.glob("Table_*.pdf")), key=lambda p: int(re.search(r"\d+", p.stem).group(0)))

counts = {"LEFT": 0, "MIDDLE": 0, "UNKNOWN": []}

for pdf_path in pdf_files:
    t_num = pdf_path.stem.replace("Table_", "")
    with pdfplumber.open(str(pdf_path)) as pdf:
        p0 = pdf.pages[0]
        words = p0.extract_words()
        
        # Find the label "Train Number" or "TRAIN"
        label_words = [w for w in words if w["text"].lower() in ("train", "trains") and w["top"] < 170]
        if not label_words:
            label_words = [w for w in words if "train" in w["text"].lower() and w["top"] < 200]
            
        if label_words:
            # find the one that is the column header label (usually preceding Number)
            label = min(label_words, key=lambda w: w["x0"])
            # if x0 < 100 -> LEFT, else MIDDLE
            if label["x0"] < 120:
                counts["LEFT"] += 1
            else:
                counts["MIDDLE"] += 1
        else:
            counts["UNKNOWN"].append(t_num)

print(f"Verified Classification: LEFT={counts['LEFT']}, MIDDLE={counts['MIDDLE']}, UNKNOWN={counts['UNKNOWN']}")
