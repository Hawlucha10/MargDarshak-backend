import json
from pathlib import Path

json_path = Path("D:/Sih58/NishkarshFoundData/Table_56_extracted_sample.json")
with open(json_path, "r", encoding="utf-8") as f:
    trains = json.load(f)

print("=========================================================================")
print("             KM & CUMULATIVE JOURNEY DISTANCE VERIFICATION               ")
print("=========================================================================")

target_trains = ["22182", "22181", "22470", "22469", "12122"]

for t_num in target_trains:
    t = next((tr for tr in trains if tr["train_number"] == t_num), None)
    if not t:
        continue
    
    print(f"\n[TRAIN] #{t['train_number']} ({t['direction']}): {t['train_name']}")
    print(f"   Route: {t['origin_station']} -> {t['destination_station']}")
    print(f"   Total Journey Distance: {t['total_distance_km']} km | Total Stops: {t['total_stops_on_table']}")
    print("   Stops Breakdown:")
    for s in t["stops"]:
        print(f"      [{s['stop_sequence']:2d}] {s['station_name']:28} ({s['station_code']:4}) | Journey KM: {s['km']:4d} km (Track: {s['track_milestone_km']:4d}) | Arr: {str(s['arrival']):8} | Dep: {str(s['departure']):8}")
