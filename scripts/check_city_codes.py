import json

with open("D:/Sih58/NishkarshFoundData/TAG_2026_complete_timetable.json", "r", encoding="utf-8") as f:
    trains = json.load(f)

# Find all station codes that are not standard 2-4 letter valid codes or look like abbreviations
stations_freq = {}
for t in trains:
    for s in t["stops"]:
        c = s["station_code"].upper()
        name = s.get("station_name", "")
        if c not in stations_freq:
            stations_freq[c] = {"count": 0, "names": set()}
        stations_freq[c]["count"] += 1
        if name:
            stations_freq[c]["names"].add(name)

# Check specific major city names
cities = ["indore", "bhopal", "jabalpur", "gwalior", "jaipur", "udaipur", "ahmedabad", "surat", "vadodara", "lucknow", "kanpur", "varanasi", "patna", "kolkata", "chennai", "bengaluru", "hyderabad", "mumbai", "delhi", "chandigarh", "amritsar", "jammu"]

for city in cities:
    matching = []
    for c, data in stations_freq.items():
        for n in data["names"]:
            if city in n.lower():
                matching.append((c, list(data["names"])[:1], data["count"]))
                break
    print(f"\nCity: {city.upper()}")
    for m in matching:
        print(f"   Code: {m[0]:6s} | Name: {m[1]} | Freq: {m[2]}")
