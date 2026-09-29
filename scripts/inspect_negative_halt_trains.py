import pdfplumber
from pathlib import Path

BASE_DIR = Path("D:/Sih58/NishkarshFoundData/Content/T")

def inspect_train(table_num, train_num):
    pdf_path = BASE_DIR / f"Table_{table_num:02d}.pdf"
    with pdfplumber.open(str(pdf_path)) as pdf:
        for p_idx, page in enumerate(pdf.pages):
            tables = page.extract_tables()
            if not tables:
                continue
            table = tables[0]
            # find which col has train_num
            target_c = None
            for r in range(min(5, len(table))):
                for c in range(len(table[r])):
                    if str(train_num) in str(table[r][c] or ""):
                        target_c = c
                        break
                if target_c is not None:
                    break
            
            if target_c is not None:
                print(f"Table {table_num:02d}, Page {p_idx+1}, Train {train_num} found in Col {target_c}:")
                for r in range(len(table)):
                    stn = str(table[r][0] or "")
                    val = str(table[r][target_c] or "")
                    # print also adjacent columns
                    adj_left = str(table[r][target_c-1] or "") if target_c > 0 else ""
                    adj_right = str(table[r][target_c+1] or "") if target_c + 1 < len(table[r]) else ""
                    if val.strip() or stn.strip():
                        print(f"  R{r:02d} [{stn:<20}] | Col {target_c-1}: {adj_left:<12} | Target: {val:<15} | Col {target_c+1}: {adj_right:<12}")

print("=== INSPECTING TRAIN 22132 IN TABLE 06 ===")
inspect_train(6, 22132)

print("\n=== INSPECTING TRAIN 14606 IN TABLE 12 ===")
inspect_train(12, 14606)
