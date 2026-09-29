import json

with open("D:/Sih58/NishkarshFoundData/TAG_2026_complete_timetable.json", "r", encoding="utf-8") as f:
    trains = json.load(f)

print(f"Total unique stitched trains: {len(trains)}")
unique_train_nums = set(t["train_number"] for t in trains)
print(f"Total distinct train numbers: {len(unique_train_nums)}")

# Look at long trains that were stitched across multiple tables
sample_trains = ["12138", "12627", "12625", "12780", "12616"]
for t in trains:
    if t["train_number"] in sample_trains:
        print(f"  Train {t['train_number']} ({t['train_name']}): {len(t['stops'])} stops from {t['stops'][0]['station_code']} to {t['stops'][-1]['station_code']}")
