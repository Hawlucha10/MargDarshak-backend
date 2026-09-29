import json
from pathlib import Path

PRIMARY_PATH = Path("D:/Sih58/NishkarshFoundData/TAG_2026_complete_timetable.json")
# Let's check how many stops trains have in raw extract_all_tables_v2
with open("D:/Sih58/NishkarshFoundData/TAG_2026_complete_timetable.json", "r", encoding="utf-8") as f:
    trains = json.load(f)

print(f"Total trains: {len(trains)}")
for t in trains[:10]:
    print(f"Train {t['train_number']}: {t['train_name']} -> {len(t['stops'])} stops: {[s['station_name'] for s in t['stops'][:5]]}")
