import pdfplumber
import re
from pathlib import Path

def detect_table_layout(table):
    """
    Detects whether stations are on the LEFT or in the MIDDLE.
    Returns:
      layout_type: 'LEFT' or 'MIDDLE'
      km_col: column index of KM
      stn_col: column index of Station Name
      down_cols: list of column indices for Down trains
      up_cols: list of column indices for Up trains
    """
    if not table or len(table) < 5:
        return None

    num_rows = len(table)
    num_cols = len(table[0])

    # Find the row containing 'Train Number' or numbers matching 5-digit trains
    train_row_idx = -1
    for r in range(min(4, num_rows)):
        row_str = " ".join([str(c or "") for c in table[r]])
        if re.search(r"\b\d{5}\b", row_str) or "train number" in row_str.lower():
            train_row_idx = r
            break

    if train_row_idx == -1:
        train_row_idx = 0

    # Look for 'Km' header
    km_col = -1
    stn_col = -1

    for r in range(min(8, num_rows)):
        for c in range(num_cols):
            cell = str(table[r][c] or "").strip().lower()
            if cell in ("km", "km.", "km 0", "kilometre", "kilometres") or cell.startswith("km"):
                km_col = c
                break
        if km_col != -1:
            break

    # If KM found, station is typically adjacent
    if km_col != -1:
        # Check col to the right
        if km_col + 1 < num_cols:
            stn_col = km_col + 1
        elif km_col - 1 >= 0:
            stn_col = km_col - 1
    else:
        # Scan for column with most text/station-like content
        max_text_len = 0
        best_c = 0
        for c in range(num_cols):
            avg_len = sum(len(str(table[r][c] or "")) for r in range(4, min(15, num_rows)))
            if avg_len > max_text_len:
                max_text_len = avg_len
                best_c = c
        stn_col = best_c
        km_col = max(0, stn_col - 1)

    # Determine if layout is LEFT or MIDDLE
    # In LEFT layout, stn_col is near the left edge (c <= 2)
    # In MIDDLE layout, stn_col is around center (e.g. 4 <= c <= 10 with trains on both sides)
    train_cols_left = [c for c in range(0, km_col) if re.search(r"\b\d{5}\b", str(table[train_row_idx][c] or ""))]
    train_cols_right = [c for c in range(max(km_col, stn_col) + 1, num_cols) if re.search(r"\b\d{5}\b", str(table[train_row_idx][c] or ""))]

    if len(train_cols_left) > 0 and len(train_cols_right) > 0:
        layout_type = "MIDDLE"
        down_cols = train_cols_left
        up_cols = train_cols_right
    else:
        layout_type = "LEFT"
        # All columns with 5-digit train numbers are trains
        train_cols = [c for c in range(num_cols) if c not in (km_col, stn_col) and re.search(r"\b\d{5}\b", str(table[train_row_idx][c] or ""))]
        down_cols = train_cols
        up_cols = []

    return {
        "layout_type": layout_type,
        "km_col": km_col,
        "stn_col": stn_col,
        "down_cols": down_cols,
        "up_cols": up_cols,
        "total_trains": len(down_cols) + len(up_cols),
    }

for t_num in [1, 2, 3, 10, 20, 56]:
    path = f"D:/Sih58/NishkarshFoundData/Content/T/Table_{t_num:02d}.pdf"
    with pdfplumber.open(path) as pdf:
        p0 = pdf.pages[0]
        tables = p0.extract_tables()
        if tables:
            info = detect_table_layout(tables[0])
            print(f"Table {t_num:02d} Page 1 -> Layout: {info['layout_type']:6} | KM Col: {info['km_col']} | Stn Col: {info['stn_col']} | Trains Detected: {info['total_trains']}")
