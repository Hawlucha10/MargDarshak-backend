import json
from pathlib import Path

with open("D:/Sih58/NishkarshFoundData/TAG_2026_complete_timetable.json", "r", encoding="utf-8") as f:
    trains = json.load(f)

for t in trains:
    for s in t.get("stops", []):
        name = s.get("station_name", "")
        if any(k in name for k in ["is l h", "M h h h", "va ir r"]):
            print(f"Table {t['table_number']}, Train {t['train_number']}: '{name}' (Stop {s['stop_sequence']})")
