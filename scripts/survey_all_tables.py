import pdfplumber
import re
from pathlib import Path

TABLES_DIR = Path("D:/Sih58/NishkarshFoundData/Content/T")

def survey_tables():
    pdf_files = sorted(list(TABLES_DIR.glob("Table_*.pdf")), key=lambda p: int(re.search(r"\d+", p.stem).group(0)))
    print(f"Surveying {len(pdf_files)} table PDFs...")
    
    layouts = {"MIDDLE": [], "LEFT": [], "OTHER": []}
    
    for pdf_path in pdf_files:
        t_num = pdf_path.stem.replace("Table_", "")
        try:
            with pdfplumber.open(str(pdf_path)) as pdf:
                p0 = pdf.pages[0]
                words = p0.extract_words()
                
                # Find train numbers
                train_words = [w for w in words if re.search(r"^\d{5}", w["text"]) and w["top"] < 150]
                if not train_words:
                    # try wider top range
                    train_words = [w for w in words if re.search(r"^\d{5}", w["text"]) and w["top"] < 220]
                
                # Find station words / table headers
                km_words = [w for w in words if w["text"].lower().startswith("km") and w["top"] < 250]
                
                if not train_words:
                    layouts["OTHER"].append((t_num, f"No train numbers found ({len(words)} words)"))
                    continue
                
                min_train_x = min(w["x0"] for w in train_words)
                max_train_x = max(w["x1"] for w in train_words)
                
                if km_words:
                    km_x = km_words[0]["x0"]
                    # If km is in the middle of train numbers:
                    trains_left = [w for w in train_words if w["x1"] < km_x]
                    trains_right = [w for w in train_words if w["x0"] > km_x]
                    if len(trains_left) > 0 and len(trains_right) > 0:
                        layouts["MIDDLE"].append(t_num)
                    else:
                        layouts["LEFT"].append(t_num)
                else:
                    if min_train_x > 100:
                        layouts["LEFT"].append(t_num)
                    else:
                        layouts["OTHER"].append((t_num, f"min_train_x={min_train_x:.1f}"))
        except Exception as e:
            layouts["OTHER"].append((t_num, str(e)))

    print(f"MIDDLE layout tables ({len(layouts['MIDDLE'])}): {layouts['MIDDLE']}")
    print(f"LEFT layout tables ({len(layouts['LEFT'])}): {layouts['LEFT']}")
    print(f"OTHER/Exceptions ({len(layouts['OTHER'])}): {layouts['OTHER']}")

if __name__ == "__main__":
    survey_tables()
