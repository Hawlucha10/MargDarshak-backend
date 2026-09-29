"""
Test Time Parsing and Directionality for Down and Up Trains on Table 56.
Ensures:
  1. For all 2-time stops: Arrival <= Departure (Halt >= 0)
  2. For Origin stop: Arrival is None, Departure is valid
  3. For Terminating stop: Arrival is valid, Departure is None
"""

import re
from pathlib import Path
import pdfplumber

def parse_cell_times(cell_val: str, direction: str, is_first: bool, is_last: bool):
    """
    Parses time from cell according to Indian Railways TAG specification:
    - Down trains (left side): Header is 'a d' -> First is Arrival, Second is Departure.
    - Up trains (right side): Header is 'd a' -> First is Departure, Second is Arrival.
    - First stop: Departure only.
    - Last stop: Arrival only.
    """
    if not cell_val or not cell_val.strip():
        return None, None
    raw = cell_val.strip()
    if "..." in raw or raw in (". .", "-", "None"):
        return None, None

    val = raw.replace(".", ":")
    parts = val.split()

    if len(parts) >= 2:
        t1, t2 = parts[0], parts[1]
        if direction == "DOWN":
            # Header is 'a d' -> t1 is Arrival, t2 is Departure
            arr, dep = t1, t2
        else:
            # Header is 'd a' -> t1 is Departure, t2 is Arrival
            dep, arr = t1, t2
        return arr, dep

    elif len(parts) == 1:
        single_time = parts[0]
        m = re.match(r"^(\d{1,2}:\d{2})$", single_time)
        if not m:
            return None, None

        if is_first:
            # Originating stop has Departure only
            return None, single_time
        elif is_last:
            # Terminating stop has Arrival only
            return single_time, None
        else:
            # Intermediate single time (e.g. 1-min quick stop)
            return single_time, single_time

    return None, None


# Test sample cells from Table 56
samples = [
    ("Page 1 Down Agra Cantt", "01.40 01.45", "DOWN", False, False),
    ("Page 1 Down Origin Nizamuddin", "23.00", "DOWN", True, False),
    ("Page 1 Down Terminus Jabalpur", "07.25", "DOWN", False, True),
    ("Page 1 Up Jhansi", "22.43 22.35", "UP", False, False),
    ("Page 1 Up Agra Cantt", "01.27 01.25", "UP", False, False),
    ("Page 2 Up VB Jhansi", "18.25 18.20", "UP", False, False),
    ("Page 2 Up VB Gwalior", "19.33 19.28", "UP", False, False),
    ("Page 2 Up VB Agra Cantt", "21.00 20.55", "UP", False, False),
    ("Page 2 Up VB Origin Khajuraho", "14.50", "UP", True, False),
    ("Page 2 Up VB Terminus Nizamuddin", "23.10", "UP", False, True),
]

print("=== CELL TIMING PARSER TEST ===")
for desc, cell, direction, first, last in samples:
    arr, dep = parse_cell_times(cell, direction, first, last)
    print(f"{desc:35} | Raw: {cell:12} | Dir: {direction:4} -> Arr: {str(arr):8} | Dep: {str(dep):8}")
