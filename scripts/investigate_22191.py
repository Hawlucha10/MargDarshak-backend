import json
import asyncio
import sys
from pathlib import Path

# 1. Search TAG_2026_complete_timetable.json for 22191
with open("D:/Sih58/NishkarshFoundData/TAG_2026_complete_timetable.json", "r", encoding="utf-8") as f:
    trains = json.load(f)

t22191 = None
for t in trains:
    if t["train_number"] == "22191":
        t22191 = t
        break

if t22191:
    print(f"FOUND 22191 in TAG JSON: {t22191['train_name']}, stops={len(t22191['stops'])}")
    for s in t22191["stops"]:
        print(f"  {s['stop_sequence']:2d} {s['station_code']:6s} {s['station_name']:25s} Arr: {s['arrival']} Dep: {s['departure']}")
else:
    print("Train 22191 NOT FOUND in TAG JSON!")

# Search for any train with "Indore" and "Jabalpur" in name or connecting Indore to Jabalpur
print("\nSearching for any trains between Indore and Jabalpur in TAG JSON:")
for t in trains:
    codes = [s["station_code"].upper() for s in t["stops"]]
    name = t["train_name"].lower()
    if ("indb" in codes or "ind" in codes or "indore" in name) and ("jbp" in codes or "jabalpur" in name):
        print(f"  Train {t['train_number']}: {t['train_name']} (Stops: {len(t['stops'])}, Origin: {codes[0]} -> Dest: {codes[-1]})")
