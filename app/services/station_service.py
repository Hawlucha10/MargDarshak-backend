"""
Station Search & Discovery Service
===================================
High-performance in-memory search and indexing across all 8,989 Indian Railway stations.
Provides sub-millisecond autocomplete matching by:
  1. Station code (e.g., 'GWL', 'NDLS', 'PUNE', 'CSMT')
  2. Station name (e.g., 'Gwalior', 'New Delhi', 'Pune', 'Bhopal')
  3. City aliases & major railway hub prioritization (e.g., 'Delhi', 'Mumbai', 'Bangalore')
  4. Satellite city nearby station suggestions (e.g., 'Noida' -> Anand Vihar, Nizamuddin)
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional
from sqlalchemy import select

from app.db.models import StationModel
from app.db.postgres import get_session_maker
from app.schemas.station import StationSearchResult

logger = logging.getLogger("margdarshak.station_service")

# Common Station Aliases (IRCTC renames / popular abbreviations)
STATION_ALIASES: Dict[str, str] = {
    "CSMT": "CSTM",      # Chhatrapati Shivaji Maharaj Terminus is often CSTM in DB
    "VT": "CSTM",        # Victoria Terminus
    "MMCT": "BCT",       # Mumbai Central
    "DLI": "DLI",        # Old Delhi
    "NZM": "NZM",        # Hazrat Nizamuddin
    "ANVT": "ANVT",      # Anand Vihar
    "NDLS": "NDLS",      # New Delhi
    "SDAH": "SDAH",      # Sealdah
    "HWH": "HWH",        # Howrah
    "MAS": "MAS",        # Chennai Central
    "SBC": "SBC",        # KSR Bengaluru
}

# Major Hub Stations in Metros (Boosted when searching by city name)
CITY_HUB_MAPPINGS: Dict[str, List[str]] = {
    "delhi": ["NDLS", "DLI", "NZM", "ANVT", "DEC", "DEE", "DSA"],
    "new delhi": ["NDLS", "DLI", "NZM", "ANVT"],
    "mumbai": ["CSTM", "BCT", "LTT", "BDTS", "DR", "TNA", "PNVL"],
    "bombay": ["CSTM", "BCT", "LTT", "BDTS"],
    "pune": ["PUNE", "SVJR", "KK", "CCH"],
    "gwalior": ["GWL", "DBA", "MRA"],
    "kolkata": ["HWH", "SDAH", "KOAA", "SHM"],
    "calcutta": ["HWH", "SDAH", "KOAA"],
    "bangalore": ["SBC", "YPR", "SMVB", "BNC"],
    "bengaluru": ["SBC", "YPR", "SMVB", "BNC"],
    "chennai": ["MAS", "MS", "PER", "TBM"],
    "madras": ["MAS", "MS"],
    "hyderabad": ["SC", "HYB", "KCG"],
    "secunderabad": ["SC", "HYB", "KCG"],
    "bhopal": ["BPL", "RKMP", "HBJ", "NSZ"],
    "ahmedabad": ["ADI", "SBT", "GER"],
    "jaipur": ["JP", "GADJ", "JPX"],
    "lucknow": ["LKO", "LJN", "BNZ"],
    "kanpur": ["CNB", "CPA"],
    "patna": ["PNBE", "RJPB", "DNR"],
    "varanasi": ["BSB", "BSBS", "DDU"],
    "agra": ["AGC", "AF", "AGA"],
}

# Satellite Cities (No direct railway station, or users search suburb)
SATELLITE_CITY_NEARBY: Dict[str, List[Dict[str, Any]]] = {
    "noida": [
        {"code": "ANVT", "name": "ANAND VIHAR TRM", "state": "Delhi", "distance_km": 11, "zone": "NR"},
        {"code": "NZM", "name": "DELHI H NIZAMUDDIN", "state": "Delhi", "distance_km": 14, "zone": "NR"},
        {"code": "NDLS", "name": "NEW DELHI", "state": "Delhi", "distance_km": 18, "zone": "NR"},
        {"code": "GZB", "name": "GHAZIABAD JN", "state": "Uttar Pradesh", "distance_km": 16, "zone": "NR"},
    ],
    "greater noida": [
        {"code": "GZB", "name": "GHAZIABAD JN", "state": "Uttar Pradesh", "distance_km": 25, "zone": "NR"},
        {"code": "ANVT", "name": "ANAND VIHAR TRM", "state": "Delhi", "distance_km": 28, "zone": "NR"},
        {"code": "NDLS", "name": "NEW DELHI", "state": "Delhi", "distance_km": 35, "zone": "NR"},
    ],
    "gurgaon": [
        {"code": "GGN", "name": "GURGAON", "state": "Haryana", "distance_km": 4, "zone": "NR"},
        {"code": "DEC", "name": "DELHI CANTT", "state": "Delhi", "distance_km": 19, "zone": "NR"},
        {"code": "NZM", "name": "DELHI H NIZAMUDDIN", "state": "Delhi", "distance_km": 31, "zone": "NR"},
        {"code": "NDLS", "name": "NEW DELHI", "state": "Delhi", "distance_km": 32, "zone": "NR"},
    ],
    "gurugram": [
        {"code": "GGN", "name": "GURGAON", "state": "Haryana", "distance_km": 4, "zone": "NR"},
        {"code": "DEC", "name": "DELHI CANTT", "state": "Delhi", "distance_km": 19, "zone": "NR"},
        {"code": "NZM", "name": "DELHI H NIZAMUDDIN", "state": "Delhi", "distance_km": 31, "zone": "NR"},
    ],
    "navi mumbai": [
        {"code": "PNVL", "name": "PANVEL", "state": "Maharashtra", "distance_km": 8, "zone": "CR"},
        {"code": "TNA", "name": "THANE", "state": "Maharashtra", "distance_km": 18, "zone": "CR"},
        {"code": "LTT", "name": "LOKMANYA TILAK TERM", "state": "Maharashtra", "distance_km": 22, "zone": "CR"},
        {"code": "CSTM", "name": "MUMBAI CST", "state": "Maharashtra", "distance_km": 32, "zone": "CR"},
    ],
}

# Major Popular Railway Hubs for Quick Selection
POPULAR_STATIONS: List[Dict[str, str]] = [
    {"code": "NDLS", "name": "NEW DELHI", "zone": "NR", "state": "Delhi"},
    {"code": "GWL", "name": "GWALIOR JN", "zone": "NCR", "state": "Madhya Pradesh"},
    {"code": "PUNE", "name": "PUNE JN", "zone": "CR", "state": "Maharashtra"},
    {"code": "CSTM", "name": "MUMBAI CST", "zone": "CR", "state": "Maharashtra"},
    {"code": "BPL", "name": "BHOPAL JN", "zone": "WCR", "state": "Madhya Pradesh"},
    {"code": "HWH", "name": "HOWRAH JN", "zone": "ER", "state": "West Bengal"},
    {"code": "SBC", "name": "KSR BENGALURU", "zone": "SWR", "state": "Karnataka"},
    {"code": "MAS", "name": "MGR CHENNAI CTL", "zone": "SR", "state": "Tamil Nadu"},
    {"code": "CNB", "name": "KANPUR CENTRAL", "zone": "NCR", "state": "Uttar Pradesh"},
    {"code": "BSB", "name": "VARANASI JN", "zone": "NR", "state": "Uttar Pradesh"},
]

_STATIONS_CACHE: List[Dict[str, Any]] = []
_STATIONS_BY_CODE: Dict[str, Dict[str, Any]] = {}
_CACHE_LOCK = asyncio.Lock()


async def initialize_stations() -> None:
    """Load all stations from PostgreSQL into in-memory fast index."""
    global _STATIONS_CACHE, _STATIONS_BY_CODE
    if _STATIONS_CACHE:
        return

    async with _CACHE_LOCK:
        if _STATIONS_CACHE:
            return

        try:
            sm = get_session_maker()
            async with sm() as db:
                result = await db.execute(select(StationModel))
                db_stations = result.scalars().all()

                cache: List[Dict[str, Any]] = []
                by_code: Dict[str, Dict[str, Any]] = {}

                for s in db_stations:
                    code = s.code.strip().upper() if s.code else ""
                    name = s.name.strip().upper() if s.name else ""
                    zone = s.zone.strip().upper() if s.zone else ""
                    state = s.state.strip() if s.state else ""
                    lat = float(s.lat) if s.lat is not None else 0.0
                    lon = float(s.lon) if s.lon is not None else 0.0

                    item = {
                        "code": code,
                        "name": name,
                        "zone": zone,
                        "state": state,
                        "lat": lat,
                        "lon": lon,
                        "is_hub": False,
                    }
                    cache.append(item)
                    by_code[code] = item

                # Mark known hubs
                all_hub_codes = set()
                for h_list in CITY_HUB_MAPPINGS.values():
                    all_hub_codes.update(h_list)
                for p in POPULAR_STATIONS:
                    all_hub_codes.add(p["code"])

                for code in all_hub_codes:
                    if code in by_code:
                        by_code[code]["is_hub"] = True

                _STATIONS_CACHE = cache
                _STATIONS_BY_CODE = by_code
                logger.info("Loaded %d stations into in-memory search index.", len(_STATIONS_CACHE))
        except Exception as e:
            logger.error("Failed to initialize stations cache from database: %s", e)


async def search_stations(query: str, limit: int = 15) -> List[StationSearchResult]:
    """
    Search stations by code prefix, exact code, station name, or city.
    Yields sorted results matching IRCTC autocomplete behavior.
    """
    await initialize_stations()

    clean_q = query.strip()
    if not clean_q:
        return [
            StationSearchResult(
                code=p["code"],
                name=p["name"],
                zone=p.get("zone"),
                state=p.get("state"),
                is_hub=True,
            )
            for p in POPULAR_STATIONS[:limit]
        ]

    q_lower = clean_q.lower()
    q_upper = clean_q.upper()

    # 1. Check satellite city matches first (e.g. "Noida", "Gurgaon")
    if q_lower in SATELLITE_CITY_NEARBY:
        satellites = SATELLITE_CITY_NEARBY[q_lower]
        return [
            StationSearchResult(
                code=s["code"],
                name=s["name"],
                zone=s.get("zone"),
                state=s.get("state"),
                distance_km=s.get("distance_km"),
                is_hub=True,
            )
            for s in satellites[:limit]
        ]

    # Check for prefix satellite match (e.g. user typed "noid")
    for sat_city, hub_list in SATELLITE_CITY_NEARBY.items():
        if sat_city.startswith(q_lower):
            return [
                StationSearchResult(
                    code=s["code"],
                    name=s["name"],
                    zone=s.get("zone"),
                    state=s.get("state"),
                    distance_km=s.get("distance_km"),
                    is_hub=True,
                )
                for s in hub_list[:limit]
            ]

    # 2. Check if query is an alias (e.g. CSMT -> CSTM)
    alias_target = STATION_ALIASES.get(q_upper)
    boosted_hub_ranks: Dict[str, int] = {}
    if q_lower in CITY_HUB_MAPPINGS:
        boosted_hub_ranks = {code: idx for idx, code in enumerate(CITY_HUB_MAPPINGS[q_lower])}
    else:
        # Check partial city match (e.g. "delh" -> "delhi")
        for city_name, hubs in CITY_HUB_MAPPINGS.items():
            if city_name.startswith(q_lower):
                boosted_hub_ranks = {code: idx for idx, code in enumerate(hubs)}
                break

    scored: List[tuple[int, int, str, Dict[str, Any]]] = []

    for s in _STATIONS_CACHE:
        code = s["code"]
        name = s["name"]
        score = 0

        # Exact code match (e.g. 'GWL' == 'GWL')
        if code == q_upper:
            score += 1500
        # Alias match (e.g. user typed 'CSMT', station code is 'CSTM')
        elif alias_target and code == alias_target:
            score += 1400
        # Code prefix match (e.g. 'ND' -> 'NDLS')
        elif code.startswith(q_upper):
            score += 900
        # Code contains query
        elif q_upper in code:
            score += 300

        # Station name checks
        if name.startswith(q_upper):
            score += 700
        elif any(w.startswith(q_upper) for w in name.split()):
            # Word starts with query, e.g. "DELHI" in "NEW DELHI"
            score += 550
        elif q_upper in name:
            score += 200

        # Hub priority boost if city matches
        if code in boosted_hub_ranks:
            rank = boosted_hub_ranks[code]
            score += max(100, 800 - rank * 60)
        elif s.get("is_hub", False) and (q_upper in name or q_upper in code):
            score += 100

        if score > 0:
            # Sort tuple: (-score, length of name for cleaner shorter matches, name)
            scored.append((-score, len(name), name, s))

    scored.sort()

    results: List[StationSearchResult] = []
    seen_codes = set()

    for item in scored[:limit]:
        s = item[3]
        if s["code"] not in seen_codes:
            seen_codes.add(s["code"])
            results.append(
                StationSearchResult(
                    code=s["code"],
                    name=s["name"],
                    zone=s.get("zone"),
                    state=s.get("state"),
                    is_hub=s.get("is_hub", False),
                )
            )

    return results


def get_popular_stations() -> List[StationSearchResult]:
    """Return top 10 major railway hubs."""
    return [
        StationSearchResult(
            code=p["code"],
            name=p["name"],
            zone=p.get("zone"),
            state=p.get("state"),
            is_hub=True,
        )
        for p in POPULAR_STATIONS
    ]
