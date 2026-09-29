import json

with open("D:/Sih58/NishkarshFoundData/TAG_2026_complete_timetable.json", "r", encoding="utf-8") as f:
    trains = json.load(f)

for t in trains:
    if t["train_number"] == "22182":
        print(f"Train: {t['train_number']} - {t['train_name']}")
        print(f"Total stops: {len(t['stops'])}")
        for s in t["stops"]:
            print(f"  Seq: {s['stop_sequence']:2d} | Stn: {s['station_code']:5s} | {s['station_name']:25s} | Arr: {s['arrival']} | Dep: {s['departure']} | Day: {s['day']} | KM: {s.get('distance_km')}")
