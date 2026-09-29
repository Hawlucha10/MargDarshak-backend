import json

with open("D:/Sih58/NishkarshFoundData/TAG_2026_complete_timetable.json", "r", encoding="utf-8") as f:
    trains = json.load(f)

for t in trains:
    if t["train_number"] == "22181":
        print(f"Train 22181: {t['train_name']}, stops={len(t['stops'])}")
        for s in t["stops"]:
            print(f"  {s['stop_sequence']:2d} {s['station_code']:5s} {s['station_name']:20s} arr={s['arrival']} dep={s['departure']}")
