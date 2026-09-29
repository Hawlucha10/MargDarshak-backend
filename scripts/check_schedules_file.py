import json
from pathlib import Path

p = Path("D:/Sih58/MargDarshak-backend/data/timetable/train_schedules.json")
if p.exists():
    print(f"File exists, size: {p.stat().st_size / (1024*1024):.2f} MB")
    with open(p, "r", encoding="utf-8") as f:
        data = json.load(f)
    print(f"Total schedule records in train_schedules.json: {len(data)}")
    train_22182 = [r for r in data if str(r.get("train_number")) == "22182"]
    print(f"Train 22182 records: {len(train_22182)}")
    for r in train_22182:
        print(f"  {r.get('station_code')} {r.get('station_name')} Arr: {r.get('arrival')} Dep: {r.get('departure')}")
else:
    print("File does not exist")
