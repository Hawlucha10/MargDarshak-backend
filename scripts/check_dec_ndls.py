import json

with open("D:/Sih58/NishkarshFoundData/TAG_2026_complete_timetable.json", "r", encoding="utf-8") as f:
    trains = json.load(f)

dec_new_delhi = []
for t in trains:
    for s in t["stops"]:
        if s["station_code"].upper() == "DEC" and any(w in (s.get("station_name") or "").lower() for w in ["new delhi", "ew delhi", "delhi"]):
            dec_new_delhi.append((t["train_number"], t["train_name"], s["station_name"]))

print(f"Total DEC stops with New Delhi in name: {len(dec_new_delhi)}")
for d in dec_new_delhi[:10]:
    print(f"  Train {d[0]:6s} {d[1]:30s} -> {d[2]}")
