"""
Bus Network Generator for MargDarshak
Generates realistic Indian intercity bus network:
  - 33 operators (25 State RTCs + 8 Private)
  - ~150 bus terminals mapped to major railway junctions
  - ~2,500 bus routes on real intercity corridors
  - ~30,000 bus delay records for ML training
"""

import asyncio
import asyncpg
import random
import math
from datetime import time as dt_time

DB_DSN = "postgresql://margdarshak:changeme_in_production@localhost:5432/margdarshak"

# ---- OPERATORS ----
STATE_RTCS = [
    ("Maharashtra SRTC", "MSRTC", "STATE_RTC", "Maharashtra", 3.8),
    ("Uttar Pradesh SRTC", "UPSRTC", "STATE_RTC", "Uttar Pradesh", 3.2),
    ("Madhya Pradesh SRTC", "MPSRTC", "STATE_RTC", "Madhya Pradesh", 3.4),
    ("Gujarat SRTC", "GSRTC", "STATE_RTC", "Gujarat", 3.9),
    ("Rajasthan SRTC", "RSRTC", "STATE_RTC", "Rajasthan", 3.6),
    ("Delhi Transport Corp", "DTC", "STATE_RTC", "Delhi", 3.0),
    ("Karnataka SRTC", "KSRTC_KA", "STATE_RTC", "Karnataka", 4.0),
    ("Kerala SRTC", "KSRTC_KL", "STATE_RTC", "Kerala", 4.1),
    ("AP SRTC", "APSRTC", "STATE_RTC", "Andhra Pradesh", 3.7),
    ("Telangana SRTC", "TSRTC", "STATE_RTC", "Telangana", 3.8),
    ("Odisha SRTC", "OSRTC", "STATE_RTC", "Odisha", 3.1),
    ("Himachal RTC", "HRTC", "STATE_RTC", "Himachal Pradesh", 3.5),
    ("Punjab RTC", "PRTC", "STATE_RTC", "Punjab", 3.3),
    ("Chandigarh TU", "CTU", "STATE_RTC", "Chandigarh", 3.6),
    ("Bihar SRTC", "BSRTC", "STATE_RTC", "Bihar", 2.8),
    ("North Bengal STC", "NBSTC", "STATE_RTC", "West Bengal", 3.0),
    ("South Bengal STC", "SBSTC", "STATE_RTC", "West Bengal", 3.1),
    ("Uttarakhand RTC", "UKRTC", "STATE_RTC", "Uttarakhand", 3.4),
    ("J&K SRTC", "JKSRTC", "STATE_RTC", "J&K", 3.2),
    ("Assam STC", "ASTC", "STATE_RTC", "Assam", 2.9),
    ("Tamil Nadu STC", "TNSTC", "STATE_RTC", "Tamil Nadu", 3.7),
    ("Kadamba TC", "KADAMBA", "STATE_RTC", "Goa", 3.8),
    ("Puducherry RTC", "PRTC_PY", "STATE_RTC", "Puducherry", 3.3),
    ("Calcutta STC", "CSTC", "STATE_RTC", "West Bengal", 2.9),
    ("Jharkhand SRTC", "JSRTC", "STATE_RTC", "Jharkhand", 2.7),
]

PRIVATE_OPS = [
    ("ZingBus", "ZINGBS", "PRIVATE", None, 4.4),
    ("IntrCity SmartBus", "INTRCY", "PRIVATE", None, 4.5),
    ("NueGo Electric", "NUEGO", "PRIVATE", None, 4.6),
    ("VRL Travels", "VRL", "PRIVATE", None, 4.2),
    ("SRS Travels", "SRS", "PRIVATE", None, 4.0),
    ("Neeta Travels", "NEETA", "PRIVATE", None, 4.1),
    ("Paulo Travels", "PAULO", "PRIVATE", None, 4.3),
    ("Orange Travels", "ORNGE", "PRIVATE", None, 3.9),
]

# ---- MAJOR JUNCTION STATIONS for bus terminals ----
# These are real major railway junction codes that have bus stands nearby
MAJOR_JUNCTIONS = [
    "PUNE", "CSTM", "LTT", "NDLS", "BCT", "ADI", "JP", "AGC", "GWL", "BPL",
    "JBP", "INDB", "NGP", "SUR", "KYN", "NMH", "PNVL", "JHS", "CNB", "LKO",
    "BSB", "PRYJ", "MB", "PDPL", "ALD", "RJT", "BRC", "ST", "UDZ", "AJJ",
    "MAS", "SBC", "HYB", "SC", "VSKP", "BZA", "GNT", "TJ", "CBE", "MDU",
    "TVC", "ERS", "CLT", "CNTL", "PTNA", "DNR", "RJPB", "HWH", "SDAH", "RNC",
    "JAT", "ASR", "CDG", "DHN", "DDN", "HW", "KGM", "GKP", "ANVT", "DEE",
    "RTM", "KTT", "ABR", "BHUJ", "NED", "AWB", "NZM", "DLI", "DSJ", "RE",
    "MYS", "HUP", "SWM", "GTL", "DWR", "UBL", "BJU", "KOP", "MRJ", "KLR",
    "PBR", "BVP", "RWL", "WL", "ET", "SJP", "NAG", "KTE", "SGO", "CPR",
    "DMO", "SGR", "BME", "JSM", "AJNI", "BD", "UHL", "KLM", "GHY", "KAJ",
    "MTJ", "FD", "BE", "SLN", "RNAC", "CNS", "DBG", "SPJ", "SEE", "BJU",
    "NJP", "KIR", "MLDT", "RPH", "BWN", "BHP", "HTE", "TATA", "CKP", "SBP",
    "BBS", "PURI", "SHM", "BAM", "ROU", "RGDA", "KUR", "BNP", "SAM", "MDP",
    "CCT", "BPQ", "WL", "ITR", "KCG", "FM", "NLR", "TPT", "RU", "BXN",
    "TEN", "NCJ", "TCR", "PGT", "QLN", "SRR", "CAN", "PYO", "MAQ", "MNG",
]

# ---- HIGH-FREQUENCY BUS CORRIDORS ----
# (from_station, to_station, avg_distance_km, hourly_frequency, operators_slice)
BUS_CORRIDORS = [
    # Maharashtra
    ("PUNE", "CSTM", 150, 4, "MSRTC"), ("PUNE", "NGP", 700, 1, "MSRTC"),
    ("PUNE", "KOP", 250, 2, "MSRTC"), ("CSTM", "NMH", 140, 3, "MSRTC"),
    ("PUNE", "SUR", 260, 2, "MSRTC"), ("PUNE", "INDB", 580, 1, "MSRTC"),
    # North India
    ("NDLS", "JP", 280, 3, "RSRTC"), ("NDLS", "AGC", 210, 4, "UPSRTC"),
    ("NDLS", "CDG", 250, 3, "CTU"), ("NDLS", "DDN", 260, 2, "UKRTC"),
    ("NDLS", "LKO", 500, 2, "UPSRTC"), ("AGC", "GWL", 120, 3, "UPSRTC"),
    ("AGC", "JP", 230, 2, "RSRTC"), ("LKO", "CNB", 80, 4, "UPSRTC"),
    ("LKO", "BSB", 300, 2, "UPSRTC"), ("LKO", "GKP", 270, 1, "UPSRTC"),
    ("CNB", "PRYJ", 200, 2, "UPSRTC"), ("GWL", "BPL", 420, 1, "MPSRTC"),
    ("JHS", "GWL", 100, 3, "MPSRTC"), ("BPL", "INDB", 190, 3, "MPSRTC"),
    ("BPL", "JBP", 330, 1, "MPSRTC"), ("JBP", "NGP", 320, 1, "MPSRTC"),
    # Gujarat / Rajasthan
    ("ADI", "ST", 260, 2, "GSRTC"), ("ADI", "BRC", 100, 4, "GSRTC"),
    ("ADI", "RJT", 220, 2, "GSRTC"), ("JP", "UDZ", 400, 1, "RSRTC"),
    ("JP", "BME", 340, 1, "RSRTC"), ("JP", "ADI", 490, 1, "RSRTC"),
    # South India
    ("SBC", "MAS", 350, 2, "KSRTC_KA"), ("SBC", "HYB", 570, 1, "KSRTC_KA"),
    ("SBC", "MYS", 150, 4, "KSRTC_KA"), ("MAS", "BZA", 280, 1, "APSRTC"),
    ("HYB", "BZA", 280, 2, "TSRTC"), ("HYB", "VSKP", 580, 1, "TSRTC"),
    ("SBC", "CBE", 370, 1, "KSRTC_KA"), ("CBE", "MDU", 230, 2, "TNSTC"),
    ("TVC", "ERS", 200, 2, "KSRTC_KL"), ("ERS", "CLT", 180, 2, "KSRTC_KL"),
    ("MAS", "CBE", 500, 1, "TNSTC"),
    # East India
    ("HWH", "PTNA", 530, 1, "SBSTC"), ("PTNA", "BSB", 240, 2, "BSRTC"),
    ("HWH", "BBS", 440, 1, "SBSTC"), ("RNC", "TATA", 130, 2, "JSRTC"),
    # Private operators on premium corridors
    ("NDLS", "JP", 280, 2, "ZINGBS"), ("NDLS", "CDG", 250, 2, "INTRCY"),
    ("PUNE", "CSTM", 150, 3, "NUEGO"), ("SBC", "MAS", 350, 1, "INTRCY"),
    ("ADI", "CSTM", 530, 1, "VRL"), ("HYB", "SBC", 570, 1, "ORNGE"),
    ("PUNE", "SBC", 850, 1, "VRL"), ("BPL", "INDB", 190, 2, "ZINGBS"),
    ("NDLS", "LKO", 500, 1, "INTRCY"), ("MAS", "SBC", 350, 1, "SRS"),
    ("NDLS", "AGC", 210, 3, "NUEGO"), ("CSTM", "ADI", 530, 1, "NEETA"),
    ("PUNE", "NGP", 700, 1, "PAULO"),
]

BUS_TYPES_BY_OP = {
    "STATE_RTC": [
        ("ORDINARY", False, False, 1.0, 3.2),
        ("EXPRESS", False, False, 1.3, 3.5),
        ("DELUXE", False, False, 1.6, 3.7),
        ("AC_SEATER", True, False, 2.0, 3.9),
        ("SUPER_DELUXE", True, False, 2.2, 4.0),
    ],
    "PRIVATE": [
        ("AC_SEATER", True, False, 2.2, 4.2),
        ("AC_SLEEPER", True, True, 2.8, 4.3),
        ("VOLVO_MULTI_AXLE", True, False, 2.5, 4.5),
        ("ELECTRIC_AC", True, False, 2.3, 4.6),
    ],
}

def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin(dlon/2)**2
    return R * 2 * math.asin(math.sqrt(a))


async def generate():
    conn = await asyncpg.connect(DB_DSN)
    print("[1/5] Connected to database")

    # Clear existing bus data
    await conn.execute("TRUNCATE TABLE bus_delay_records, bus_routes, bus_terminals, bus_operators RESTART IDENTITY CASCADE;")
    print("[1/5] Cleared existing bus data")

    # ---- OPERATORS ----
    print("[2/5] Inserting operators...")
    op_records = []
    for name, code, otype, state, rating in STATE_RTCS:
        op_records.append((name, code, otype, state, None, rating, False))
    for name, code, otype, state, rating in PRIVATE_OPS:
        op_records.append((name, code, otype, state, None, rating, True))

    await conn.copy_records_to_table('bus_operators',
        columns=['name', 'short_code', 'operator_type', 'state', 'website', 'rating', 'has_live_tracking'],
        records=op_records)

    # Build operator lookup
    op_rows = await conn.fetch("SELECT operator_id, short_code, operator_type FROM bus_operators")
    op_lookup = {r['short_code']: (r['operator_id'], r['operator_type']) for r in op_rows}
    print(f"  -> {len(op_rows)} operators inserted")

    # ---- TERMINALS ----
    print("[3/5] Generating bus terminals...")
    # Fetch station coords for major junctions
    placeholders = ", ".join(f"${i+1}" for i in range(len(MAJOR_JUNCTIONS)))
    station_rows = await conn.fetch(
        f"SELECT code, name, state, lat, lon FROM stations WHERE code IN ({placeholders})",
        *MAJOR_JUNCTIONS
    )
    station_map = {r['code']: r for r in station_rows}

    terminal_records = []
    for code in MAJOR_JUNCTIONS:
        if code not in station_map:
            continue
        st = station_map[code]
        lat_offset = random.uniform(-0.015, 0.015)
        lon_offset = random.uniform(-0.015, 0.015)
        t_lat = float(st['lat']) + lat_offset
        t_lon = float(st['lon']) + lon_offset
        walk_min = random.choice([8, 10, 12, 15, 18, 20, 25])
        ttype = random.choice(["ISBT", "BUS_STAND", "DEPOT"])
        amenities = random.sample(["Waiting Hall", "Restroom", "Food Stall", "ATM", "Charging Point", "Luggage Counter", "Pharmacy"], k=random.randint(2, 5))
        terminal_records.append((
            f"{st['name']} Bus Terminal",
            st['name'],
            st['state'],
            t_lat,
            t_lon,
            code,
            walk_min,
            ttype,
            amenities,
        ))

    await conn.copy_records_to_table('bus_terminals',
        columns=['name', 'city', 'state', 'lat', 'lon', 'nearest_station_code', 'transfer_walk_minutes', 'terminal_type', 'amenities'],
        records=terminal_records)

    # Update geom column
    await conn.execute("UPDATE bus_terminals SET geom = ST_SetSRID(ST_MakePoint(lon, lat), 4326) WHERE geom IS NULL;")

    term_rows = await conn.fetch("SELECT terminal_id, nearest_station_code, lat, lon FROM bus_terminals")
    term_lookup = {r['nearest_station_code']: r for r in term_rows}
    print(f"  -> {len(term_rows)} terminals inserted")

    # ---- ROUTES ----
    print("[4/5] Generating bus routes...")
    route_records = []
    route_count = 0

    # 1. Bidirectional corridors from BUS_CORRIDORS
    expanded_corridors = []
    for from_stn, to_stn, avg_dist, freq, op_code in BUS_CORRIDORS:
        expanded_corridors.append((from_stn, to_stn, avg_dist, freq, op_code))
        expanded_corridors.append((to_stn, from_stn, avg_dist, freq, op_code))

    for from_stn, to_stn, avg_dist, freq, op_code in expanded_corridors:
        if from_stn not in term_lookup or to_stn not in term_lookup:
            continue
        if op_code not in op_lookup:
            continue

        from_term = term_lookup[from_stn]
        to_term = term_lookup[to_stn]
        op_id, op_type = op_lookup[op_code]

        actual_dist = haversine(
            float(from_term['lat']), float(from_term['lon']),
            float(to_term['lat']), float(to_term['lon'])
        )
        road_dist = int(actual_dist * 1.3)
        if road_dist < 20:
            road_dist = avg_dist

        bus_types = BUS_TYPES_BY_OP.get(op_type, BUS_TYPES_BY_OP["STATE_RTC"])
        num_departures = freq * random.randint(3, 5)
        for _ in range(num_departures):
            bt_name, is_ac, is_sleeper, fare_mult, bt_rating = random.choice(bus_types)
            dep_hour = random.randint(4, 23)
            dep_min = random.choice([0, 15, 30, 45])
            avg_speed = 55 if is_ac else 42
            dur_minutes = max(60, int((road_dist / avg_speed) * 60) + random.randint(-15, 30))
            arr_total = dep_hour * 60 + dep_min + dur_minutes
            arr_hour = (arr_total // 60) % 24
            arr_min = arr_total % 60
            base_fare_per_km = 1.2 if op_type == "STATE_RTC" else 1.8
            fare = max(50, int(road_dist * base_fare_per_km * fare_mult))
            route_code = f"{op_code[:3]}{random.randint(100, 999)}"
            rating = round(bt_rating + random.uniform(-0.3, 0.3), 1)
            rating = min(5.0, max(2.0, rating))
            has_charging = is_ac and random.random() > 0.4
            has_wifi = op_type == "PRIVATE" and random.random() > 0.5

            route_records.append((
                op_id, route_code,
                from_term['terminal_id'], to_term['terminal_id'],
                bt_name,
                dt_time(dep_hour, dep_min),
                dt_time(arr_hour, arr_min),
                dur_minutes, road_dist, fare,
                "DAILY",
                is_ac, is_sleeper, has_charging, has_wifi,
                rating,
            ))
            route_count += 1

    # 2. Regional intercity connections between nearby terminals (< 500 km)
    term_list = list(term_rows)
    all_op_keys = list(op_lookup.keys())
    for _ in range(1800):
        t1, t2 = random.sample(term_list, 2)
        dist = haversine(float(t1['lat']), float(t1['lon']), float(t2['lat']), float(t2['lon']))
        if 40 <= dist <= 500:
            road_dist = int(dist * 1.3)
            op_code = random.choice(all_op_keys)
            op_id, op_type = op_lookup[op_code]
            bus_types = BUS_TYPES_BY_OP.get(op_type, BUS_TYPES_BY_OP["STATE_RTC"])
            bt_name, is_ac, is_sleeper, fare_mult, bt_rating = random.choice(bus_types)

            dep_hour = random.randint(5, 22)
            dep_min = random.choice([0, 15, 30, 45])
            avg_speed = 52 if is_ac else 40
            dur_minutes = max(60, int((road_dist / avg_speed) * 60) + random.randint(-10, 20))
            arr_total = dep_hour * 60 + dep_min + dur_minutes
            arr_hour = (arr_total // 60) % 24
            arr_min = arr_total % 60
            base_fare_per_km = 1.2 if op_type == "STATE_RTC" else 1.8
            fare = max(60, int(road_dist * base_fare_per_km * fare_mult))
            route_code = f"BUS{random.randint(1000, 9999)}"
            rating = round(bt_rating + random.uniform(-0.4, 0.4), 1)
            rating = min(5.0, max(2.0, rating))

            route_records.append((
                op_id, route_code,
                t1['terminal_id'], t2['terminal_id'],
                bt_name,
                dt_time(dep_hour, dep_min),
                dt_time(arr_hour, arr_min),
                dur_minutes, road_dist, fare,
                "DAILY",
                is_ac, is_sleeper, is_ac and random.random() > 0.5, op_type == "PRIVATE" and random.random() > 0.6,
                rating,
            ))
            route_count += 1

    await conn.copy_records_to_table('bus_routes',
        columns=['operator_id', 'route_code', 'from_terminal_id', 'to_terminal_id',
                 'bus_type', 'departure', 'arrival', 'duration_minutes', 'distance_km',
                 'fare', 'frequency', 'is_ac', 'is_sleeper', 'has_charging', 'has_wifi', 'rating'],
        records=route_records)
    print(f"  -> {route_count} bus routes inserted")

    # ---- DELAY RECORDS ----
    print("[5/5] Generating bus delay records...")
    routes_for_delay = await conn.fetch("""
        SELECT r.route_id, r.distance_km, r.bus_type, r.departure,
               o.operator_type, o.short_code
        FROM bus_routes r
        JOIN bus_operators o ON r.operator_id = o.operator_id
    """)

    if not routes_for_delay:
        print("  -> No routes found, skipping delays")
        await conn.close()
        return

    delay_records = []
    for _ in range(30000):
        r = random.choice(routes_for_delay)
        month = random.randint(1, 12)
        dow = random.randint(1, 7)
        dep_hr = r['departure'].hour

        is_fog = month in [12, 1, 2]
        is_monsoon = month in [6, 7, 8, 9]
        is_urban = r['distance_km'] < 100
        is_highway = r['distance_km'] >= 100

        # Traffic congestion index
        tci = 1.0
        if is_urban:
            tci += random.uniform(0.3, 1.5)
        if dep_hr in [8, 9, 17, 18, 19]:  # rush hours
            tci += random.uniform(0.2, 0.8)
        if dow in [6, 7]:  # weekend
            tci -= 0.1
        tci = max(0.5, min(3.0, tci + random.uniform(-0.2, 0.2)))

        # Delay probability
        base_prob = 0.25
        if r['operator_type'] == 'STATE_RTC':
            base_prob += 0.10
        if is_monsoon:
            base_prob += 0.15
        if is_fog:
            base_prob += 0.20
        if tci > 1.5:
            base_prob += 0.10

        is_delayed = random.random() < min(0.85, base_prob)
        if is_delayed:
            base_delay = int(r['distance_km'] * 0.05 * tci)
            if is_fog:
                base_delay += random.randint(20, 120)
            if is_monsoon:
                base_delay += random.randint(10, 60)
            delay_min = max(5, base_delay + random.randint(-10, 30))
        else:
            delay_min = 0

        delay_records.append((
            r['route_id'], r['operator_type'], r['bus_type'],
            r['distance_km'], month, dow, dep_hr,
            is_highway, is_urban, is_monsoon, is_fog,
            round(tci, 2), delay_min, is_delayed
        ))

    await conn.copy_records_to_table('bus_delay_records',
        columns=['route_id', 'operator_type', 'bus_type', 'route_distance_km',
                 'month', 'day_of_week', 'departure_hour', 'is_highway',
                 'is_urban_stretch', 'is_monsoon', 'is_fog_risk',
                 'traffic_congestion_index', 'delay_minutes', 'is_delayed'],
        records=delay_records)
    print(f"  -> 30,000 bus delay records inserted")

    # Final counts
    counts = await conn.fetchrow("""
        SELECT
            (SELECT count(*) FROM bus_operators) as operators,
            (SELECT count(*) FROM bus_terminals) as terminals,
            (SELECT count(*) FROM bus_routes) as routes,
            (SELECT count(*) FROM bus_delay_records) as delays
    """)
    print(f"\n=== BUS NETWORK GENERATION COMPLETE ===")
    print(f"  Operators:     {counts['operators']}")
    print(f"  Terminals:     {counts['terminals']}")
    print(f"  Routes:        {counts['routes']}")
    print(f"  Delay Records: {counts['delays']}")

    await conn.close()


if __name__ == "__main__":
    asyncio.run(generate())
