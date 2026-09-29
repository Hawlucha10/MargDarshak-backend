import json
from pathlib import Path

json_path = Path("D:/Sih58/NishkarshFoundData/Table_56_extracted_sample.json")
with open(json_path, "r", encoding="utf-8") as f:
    trains = json.load(f)

print("=========================================================================")
print("                   SCHEDULE TIMINGS INTEGRITY AUDIT                      ")
print("=========================================================================")
errors = 0
checked_stops = 0

for t in trains:
    t_num = t["train_number"]
    t_dir = t["direction"]
    t_name = t["train_name"]
    stops = t["stops"]
    
    for idx, s in enumerate(stops):
        checked_stops += 1
        stn = s["station_name"]
        arr = s["arrival"]
        dep = s["departure"]
        seq = s["stop_sequence"]
        
        # Rule 1: Origin stop should have arrival == None
        if idx == 0 and arr is not None:
            print(f"[ERROR Origin Arr] Train {t_num} ({t_dir}): First stop '{stn}' has Arrival={arr}")
            errors += 1
            
        # Rule 2: Destination stop should have departure == None
        if idx == len(stops) - 1 and dep is not None:
            print(f"[ERROR Dest Dep] Train {t_num} ({t_dir}): Last stop '{stn}' has Departure={dep}")
            errors += 1
            
        # Rule 3: Intermediate stop should have Arr <= Dep
        if arr and dep:
            try:
                arr_parts = [int(x) for x in arr.split(":")[:2]]
                dep_parts = [int(x) for x in dep.split(":")[:2]]
                arr_min = arr_parts[0] * 60 + arr_parts[1]
                dep_min = dep_parts[0] * 60 + dep_parts[1]
                
                # Check for negative halt (departure before arrival)
                if dep_min < arr_min and (dep_min + 1440 - arr_min) > 60:
                    print(f"[ERROR Dep < Arr] Train {t_num} ({t_dir}) at '{stn}': Arr={arr} > Dep={dep}")
                    errors += 1
            except Exception as e:
                print(f"[ERROR Time Parse] Train {t_num} at '{stn}': {e}")
                errors += 1

print(f"\nAudit complete across {len(trains)} trains and {checked_stops} stops.")
print(f"Total Timing Inconsistencies Found: {errors}")
if errors == 0:
    print("SUCCESS: 100% OF ALL STOPS HAVE ZERO ERRORS (Arr <= Dep, Origin has no Arr, Dest has no Dep)!")

print("\n" + "=" * 75)
print("  VERIFIED UP TRAIN: VANDE BHARAT 22469 (Khajuraho -> Nizamuddin)")
print("=" * 75)
vb = next(t for t in trains if t["train_number"] == "22469")
for s in vb["stops"]:
    print(f"  [{s['stop_sequence']:2d}] {s['station_name']:28} | KM={s['km']:3d} | Arr={str(s['arrival']):10} | Dep={str(s['departure']):10}")

print("\n" + "=" * 75)
print("  VERIFIED DOWN TRAIN: VANDE BHARAT 22470 (Nizamuddin -> Khajuraho)")
print("=" * 75)
vb_down = next(t for t in trains if t["train_number"] == "22470")
for s in vb_down["stops"]:
    print(f"  [{s['stop_sequence']:2d}] {s['station_name']:28} | KM={s['km']:3d} | Arr={str(s['arrival']):10} | Dep={str(s['departure']):10}")
