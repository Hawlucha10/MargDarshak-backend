import json

with open("D:/Sih58/NishkarshFoundData/TAG_2026_complete_timetable.json", "r", encoding="utf-8") as f:
    trains = json.load(f)

empty_stops = []
for t in trains:
    for s in t["stops"]:
        if not s.get("station_code", "").strip():
            empty_stops.append((t["train_number"], s))

print(f"Total stops with empty station_code: {len(empty_stops)}")
for tr_num, st in empty_stops[:15]:
    print(f"  Train {tr_num}: name={st.get('station_name')}, arr={st.get('arrival')}, dep={st.get('departure')}, km={st.get('distance_km')}")
