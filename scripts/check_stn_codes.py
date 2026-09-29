import json

with open("D:/Sih58/NishkarshFoundData/TAG_2026_complete_timetable.json", "r", encoding="utf-8") as f:
    trains = json.load(f)

alias_check = ["HNZM", "NZM", "SAGO", "SGO", "VGLB", "VGLJ", "JHS", "AGC", "NDLS", "DLI"]
counts = {c: 0 for c in alias_check}

for t in trains:
    for s in t["stops"]:
        c = s["station_code"].upper()
        if c in counts:
            counts[c] += 1

print("Station code occurrences in TAG_2026_complete_timetable.json:")
for c, cnt in counts.items():
    print(f"  {c}: {cnt}")
