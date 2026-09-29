"""
Comprehensive Audit Script for TAG_2026_complete_timetable.json
Performs deep structural, semantic, and relational audits across all 4,666 trains.
"""

import json
import re
from collections import Counter, defaultdict
from pathlib import Path

JSON_PATH = Path("d:/Yue/Ura/Sih 58/NishkarshFoundData/TAG_2026_complete_timetable.json")

def audit():
    if not JSON_PATH.exists():
        print(f"Error: {JSON_PATH} not found!")
        return

    with open(JSON_PATH, "r", encoding="utf-8") as f:
        trains = json.load(f)

    total_trains = len(trains)
    print("=" * 80)
    print(f"COMPREHENSIVE AUDIT REPORT FOR: {JSON_PATH.name}")
    print(f"Total Train Schedules: {total_trains}")
    print("=" * 80)

    # 1. Station Name & Code Audit
    all_stations = Counter()
    station_code_map = {}
    garbled_stations = Counter()
    trailing_marker_stations = Counter()
    fallback_code_stations = Counter()
    empty_name_stops = 0

    # 2. Timing Audit
    negative_halt_stops = []
    both_none_stops = []
    origin_has_arrival = []
    dest_has_departure = []
    invalid_time_format_stops = []

    # 3. Distance (KM) Audit
    km_not_starting_zero = []
    non_monotonic_km_trains = []
    total_km_zero_trains = []
    large_km_jumps = []

    # 4. Train Metadata Audit
    invalid_train_numbers = []
    train_num_counts = Counter()
    unresolved_train_names = []
    short_route_trains = [] # <= 1 stop

    total_stops = 0

    time_regex = re.compile(r"^\d{2}:\d{2}:\d{2}$")

    for t_idx, train in enumerate(trains):
        t_num = train.get("train_number", "")
        t_name = train.get("train_name", "")
        t_dir = train.get("direction", "")
        t_table = train.get("table_number", "")
        train_num_counts[t_num] += 1

        if not re.match(r"^\d{5}$", str(t_num)):
            invalid_train_numbers.append((t_num, t_table))

        if t_name.startswith("Train ") and t_name[6:].isdigit():
            unresolved_train_names.append((t_num, t_name, t_table))

        stops = train.get("stops", [])
        total_stops += len(stops)

        if len(stops) <= 1:
            short_route_trains.append((t_num, t_table, len(stops)))

        prev_km = -1
        prev_dep_min = -1

        for s_idx, stop in enumerate(stops):
            s_seq = stop.get("stop_sequence", s_idx + 1)
            s_name = stop.get("station_name", "")
            s_code = stop.get("station_code", "")
            s_km = stop.get("km", 0)
            arr = stop.get("arrival")
            dep = stop.get("departure")
            day = stop.get("day", 1)

            # Check station name
            if not s_name:
                empty_name_stops += 1
            else:
                all_stations[s_name] += 1
                station_code_map[s_name] = s_code

                # Trailing markers ' a', ' d', ' a d', ' d a', ' km', etc.
                if re.search(r"\b[ad]\b", s_name) or s_name.endswith(" a") or s_name.endswith(" d") or s_name.endswith(" a d"):
                    trailing_marker_stations[s_name] += 1

                # Garbled / interleaved words: 3+ single letter words in sequence
                if re.search(r"\b[a-zA-Z]\s+[a-zA-Z]\s+[a-zA-Z]\b", s_name):
                    garbled_stations[s_name] += 1

                # Suspicious fallback code (e.g. 4 chars with trailing space or punctuation)
                if s_code == s_name[:4].upper():
                    fallback_code_stations[s_name] += 1

            # Check KM
            if s_idx == 0:
                if s_km != 0:
                    km_not_starting_zero.append((t_num, t_table, s_km))
            else:
                if s_km < prev_km:
                    non_monotonic_km_trains.append((t_num, t_table, s_idx, prev_km, s_km))
                elif s_km - prev_km > 600:
                    large_km_jumps.append((t_num, t_table, stops[s_idx-1]["station_name"], s_name, prev_km, s_km))

            prev_km = s_km

            # Check Times
            if s_idx == 0:
                if arr is not None:
                    origin_has_arrival.append((t_num, t_table, arr))
            if s_idx == len(stops) - 1:
                if dep is not None:
                    dest_has_departure.append((t_num, t_table, dep))

            if arr is None and dep is None:
                both_none_stops.append((t_num, t_table, s_name))

            if arr and not time_regex.match(arr):
                invalid_time_format_stops.append((t_num, t_table, s_name, arr))
            if dep and not time_regex.match(dep):
                invalid_time_format_stops.append((t_num, t_table, s_name, dep))

            # Negative halt check (arr > dep on same day)
            if arr and dep:
                ah, am = map(int, arr.split(":")[:2])
                dh, dm = map(int, dep.split(":")[:2])
                a_total = ah * 60 + am
                d_total = dh * 60 + dm
                # Halt crossing midnight is possible (e.g., arr 23:55, dep 00:05), but within day d_total < a_total is invalid
                if d_total < a_total:
                    # check if halt crossed midnight
                    if not (a_total >= 22 * 60 and d_total <= 2 * 60):
                        negative_halt_stops.append((t_num, t_table, s_name, arr, dep))

        if stops and stops[-1].get("km", 0) == 0:
            total_km_zero_trains.append((t_num, t_table))

    # REPORT RESULTS
    print("\n--- 1. STATION ISSUES ---")
    print(f"Total Unique Station Names: {len(all_stations)}")
    print(f"Trailing Marker Names (' a', ' d', etc.): {len(trailing_marker_stations)} unique stations ({sum(trailing_marker_stations.values())} occurrences)")
    if trailing_marker_stations:
        print("  Sample Trailing Markers:")
        for name, cnt in trailing_marker_stations.most_common(10):
            print(f"    - '{name}' (x{cnt})")

    print(f"\nGarbled/Interleaved Station Names: {len(garbled_stations)} unique stations ({sum(garbled_stations.values())} occurrences)")
    if garbled_stations:
        print("  Sample Garbled Stations:")
        for name, cnt in garbled_stations.most_common(10):
            print(f"    - '{name}' (x{cnt})")

    print(f"\nStations using raw slice fallback code (e.g. NAME[:4]): {len(fallback_code_stations)} unique stations")
    if fallback_code_stations:
        print("  Sample Fallback Codes:")
        for name, cnt in fallback_code_stations.most_common(10):
            print(f"    - '{name}' -> code: '{station_code_map.get(name)}'")

    print("\n--- 2. TIMING ISSUES ---")
    print(f"Stops with departure earlier than arrival (Negative Halts): {len(negative_halt_stops)}")
    if negative_halt_stops:
        print("  Sample Negative Halts:")
        for item in negative_halt_stops[:10]:
            print(f"    - Train {item[0]} (T{item[1]}) at {item[2]}: Arr {item[3]} > Dep {item[4]}")

    print(f"Origin stops having arrival != None: {len(origin_has_arrival)}")
    print(f"Destination stops having departure != None: {len(dest_has_departure)}")
    print(f"Stops with both arrival and departure as None: {len(both_none_stops)}")
    print(f"Stops with invalid time format: {len(invalid_time_format_stops)}")

    print("\n--- 3. DISTANCE (KM) ISSUES ---")
    print(f"Trains where first stop KM != 0: {len(km_not_starting_zero)}")
    print(f"Trains with non-monotonic KM (KM going backward): {len(non_monotonic_km_trains)}")
    if non_monotonic_km_trains:
        print("  Sample Non-monotonic KM:")
        for item in non_monotonic_km_trains[:5]:
            print(f"    - Train {item[0]} (T{item[1]}) stop {item[2]}: {item[3]} km -> {item[4]} km")
    print(f"Trains where total journey distance is 0 km: {len(total_km_zero_trains)}")
    print(f"Large KM jumps (> 600km): {len(large_km_jumps)}")
    if large_km_jumps:
        print("  Sample Large KM Jumps:")
        for item in large_km_jumps[:5]:
            print(f"    - Train {item[0]} (T{item[1]}): {item[2]} ({item[4]}km) -> {item[3]} ({item[5]}km)")

    print("\n--- 4. TRAIN METADATA ISSUES ---")
    print(f"Invalid train numbers (non-5-digit): {len(invalid_train_numbers)}")
    print(f"Unresolved train names ('Train XXXXX'): {len(unresolved_train_names)}")
    if unresolved_train_names:
        print("  Sample Unresolved Train Names:")
        for item in unresolved_train_names[:5]:
            print(f"    - Train {item[0]} (T{item[2]}): {item[1]}")
    print(f"Trains with <= 1 stop: {len(short_route_trains)}")

    duplicates = {num: count for num, count in train_num_counts.items() if count > 1}
    print(f"Duplicate train entries across tables: {len(duplicates)} train numbers appear multiple times")
    if duplicates:
        print("  Sample Duplicate Train Numbers:")
        for num, cnt in list(duplicates.items())[:10]:
            print(f"    - Train {num} appears in {cnt} tables/directions")

    print("=" * 80)

if __name__ == "__main__":
    audit()
