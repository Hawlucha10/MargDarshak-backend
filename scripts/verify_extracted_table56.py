import json
from pathlib import Path

json_path = Path("D:/Sih58/NishkarshFoundData/Table_56_extracted_sample.json")
with open(json_path, "r", encoding="utf-8") as f:
    trains = json.load(f)

print("=========================================================================")
print("  CORRECTED TABLE 56 EXTRACTION VERIFICATION (STATIONS, KM & TIMINGS)")
print("=========================================================================")

for t in trains:
    if t["train_number"] in ("22470", "12122", "19666"):
        print(f"\nTrain #{t['train_number']}: {t['train_name']}")
        print(f"Total Corridor Distance: {t['total_distance_km']} km | Stops Count: {t['total_stops_on_table']}")
        for s in t["stops"]:
            stn = s["station_name"]
            code = s["station_code"]
            km = s["km"]
            arr = s["arrival"]
            dep = s["departure"]
            print(f"   [{s['stop_sequence']:2d}] {stn:28} ({code:4}) | KM: {km:4d} | Arr: {arr} | Dep: {dep}")
