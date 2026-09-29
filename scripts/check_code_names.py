import json

with open("D:/Sih58/NishkarshFoundData/TAG_2026_complete_timetable.json", "r", encoding="utf-8") as f:
    trains = json.load(f)

code_to_name = {}
for t in trains:
    for s in t["stops"]:
        c = s["station_code"].upper()
        name = s["station_name"]
        if c not in code_to_name:
            code_to_name[c] = set()
        code_to_name[c].add(name)

sample = ["DDU", "VGLJ", "RAJA", "TIRU", "KSRB", "HAZU", "DHAR", "TUMA", "MYSU", "ALAP", "SAGO", "KALA", "MOKA", "MUMB", "LONA", "VRID", "NEWA", "RING", "DAVA", "USLA", "NEWB", "BENG", "KANN", "MIDN", "LOKM", "MIRY", "SISW", "SAMD", "VIJA", "HNZM"]

for c in sample:
    print(f"{c:6s}: {list(code_to_name.get(c, []))[:3]}")
