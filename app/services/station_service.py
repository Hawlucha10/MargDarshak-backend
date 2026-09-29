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
    "IND": "INDB",
    "INDORE": "INDB",
    "INDM": "INDB",
    "JBP": "JBP",
    "JABALPUR": "JBP",
    "PRAYAGRAJ": "PRYJ",
    "ALLAHABAD": "PRYJ",
    "ALD": "PRYJ",
    "AYODHYA": "AY",
    "AYC": "AY",
    "VARANASI": "BSB",
    "BANARAS": "BSBS",
    "MUV": "BSBS",
    "MUGHALSARAI": "DDU",
    "MGS": "DDU",
    "AHMEDABAD": "ADI",
    "ADIJ": "ADI",
    "HABIBGANJ": "RKMP",
    "HBJ": "RKMP",
    "RANI KAMALAPATI": "RKMP",
    "SMVT": "SMVB",
    "SMVT BENGALURU": "SMVB",
    "BANDRA": "BDTS",
    "KATRA": "SVDK",
    "SHIRDI": "SNSI",
    "HUBLI": "UBL",
    "MANGALORE": "MAQ",
    "AMBALA": "UMB",
    "TATANAGAR": "TATA",
    "JAMSHEDPUR": "TATA",
    "BINA": "BINA",
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
    "bhopal": ["BPL", "RKMP", "SHRN", "HBJ"],
    "indore": ["INDB", "DWX", "UJN"],
    "jabalpur": ["JBP", "MML", "KTE"],
    "prayagraj": ["PRYJ", "PCOI", "PRRB"],
    "allahabad": ["PRYJ", "PCOI", "PRRB"],
    "varanasi": ["BSB", "BSBS", "DDU"],
    "banaras": ["BSBS", "BSB", "DDU"],
    "lucknow": ["LKO", "LJN", "GTNR", "BNZ"],
    "kanpur": ["CNB", "CPA"],
    "patna": ["PNBE", "RJPB", "DNR"],
    "ahmedabad": ["ADI", "SBT"],
    "jaipur": ["JP", "GADJ", "JPX"],
    "agra": ["AGC", "AF", "AGA"],
    "surat": ["ST", "UDN"],
    "vadodara": ["BRC"],
    "nagpur": ["NGP", "AJNI"],
    "amritsar": ["ASR"],
    "chandigarh": ["CDG"],
    "shirdi": ["SNSI", "KPG", "MMR"],
    "katra": ["SVDK", "JAT"],
    "vaishno devi": ["SVDK", "JAT"],
    "hubli": ["UBL"],
    "hubballi": ["UBL"],
    "mangalore": ["MAJN", "MAQ"],
    "mangaluru": ["MAJN", "MAQ"],
    "tatanagar": ["TATA"],
    "jamshedpur": ["TATA"],
    "ambala": ["UMB"],
    "pathankot": ["PTKC"],
    "aurangabad": ["AWB"],
    "sambhaji nagar": ["AWB"],
    "ahmednagar": ["ANG"],
    "ahilyanagar": ["ANG"],
    "bina": ["BINA"],
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
    """Load all stations from PostgreSQL into in-memory fast index, annotated with active timetable stop counts."""
    global _STATIONS_CACHE, _STATIONS_BY_CODE
    if _STATIONS_CACHE:
        return

    async with _CACHE_LOCK:
        if _STATIONS_CACHE:
            return

        try:
            sm = get_session_maker()
            async with sm() as db:
                # Query all stations
                result = await db.execute(select(StationModel))
                db_stations = result.scalars().all()

                # Query active train stop counts per station
                from sqlalchemy import text
                counts_res = await db.execute(text("SELECT station_code, count(*) FROM timetable GROUP BY station_code"))
                stop_counts: Dict[str, int] = {r[0]: r[1] for r in counts_res.fetchall()}

                cache: List[Dict[str, Any]] = []
                by_code: Dict[str, Dict[str, Any]] = {}

                for s in db_stations:
                    code = s.code.strip().upper() if s.code else ""
                    name = s.name.strip().upper() if s.name else ""
                    zone = s.zone.strip().upper() if s.zone else ""
                    state = s.state.strip() if s.state else ""
                    lat = float(s.lat) if s.lat is not None else 0.0
                    lon = float(s.lon) if s.lon is not None else 0.0
                    stops = stop_counts.get(code, 0)

                    item = {
                        "code": code,
                        "name": name,
                        "zone": zone,
                        "state": state,
                        "lat": lat,
                        "lon": lon,
                        "stop_count": stops,
                        "is_hub": (stops >= 15),
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
                logger.info("Loaded %d stations into in-memory search index (%d active in timetable).", 
                            len(_STATIONS_CACHE), len(stop_counts))
        except Exception as e:
            logger.warning("Database unavailable (%s); initializing fallback station directory", e)
            _initialize_fallback_stations()


def _initialize_fallback_stations() -> None:
    """Populate in-memory station index with comprehensive fallback catalog if DB is unreachable."""
    global _STATIONS_CACHE, _STATIONS_BY_CODE
    if _STATIONS_CACHE:
        return

    fallback_stations = [
        {"code": "NDLS", "name": "NEW DELHI", "zone": "NR", "state": "Delhi", "lat": 28.6424, "lon": 77.2195, "stop_count": 350, "is_hub": True},
        {"code": "GWL", "name": "GWALIOR JN", "zone": "NCR", "state": "Madhya Pradesh", "lat": 26.2183, "lon": 78.1828, "stop_count": 180, "is_hub": True},
        {"code": "PUNE", "name": "PUNE JN", "zone": "CR", "state": "Maharashtra", "lat": 18.5289, "lon": 73.8744, "stop_count": 220, "is_hub": True},
        {"code": "CSTM", "name": "MUMBAI CST", "zone": "CR", "state": "Maharashtra", "lat": 18.9401, "lon": 72.8354, "stop_count": 290, "is_hub": True},
        {"code": "BPL", "name": "BHOPAL JN", "zone": "WCR", "state": "Madhya Pradesh", "lat": 23.2662, "lon": 77.4124, "stop_count": 210, "is_hub": True},
        {"code": "HWH", "name": "HOWRAH JN", "zone": "ER", "state": "West Bengal", "lat": 22.5840, "lon": 88.3426, "stop_count": 310, "is_hub": True},
        {"code": "SBC", "name": "KSR BENGALURU", "zone": "SWR", "state": "Karnataka", "lat": 12.9781, "lon": 77.5696, "stop_count": 190, "is_hub": True},
        {"code": "MAS", "name": "MGR CHENNAI CTL", "zone": "SR", "state": "Tamil Nadu", "lat": 13.0827, "lon": 80.2755, "stop_count": 240, "is_hub": True},
        {"code": "CNB", "name": "KANPUR CENTRAL", "zone": "NCR", "state": "Uttar Pradesh", "lat": 26.4547, "lon": 80.3507, "stop_count": 380, "is_hub": True},
        {"code": "BSB", "name": "VARANASI JN", "zone": "NR", "state": "Uttar Pradesh", "lat": 25.3268, "lon": 82.9863, "stop_count": 160, "is_hub": True},
        {"code": "DLI", "name": "OLD DELHI", "zone": "NR", "state": "Delhi", "lat": 28.6617, "lon": 77.2307, "stop_count": 190, "is_hub": True},
        {"code": "NZM", "name": "DELHI H NIZAMUDDIN", "zone": "NR", "state": "Delhi", "lat": 28.5888, "lon": 77.2534, "stop_count": 170, "is_hub": True},
        {"code": "ANVT", "name": "ANAND VIHAR TRM", "zone": "NR", "state": "Delhi", "lat": 28.6503, "lon": 77.3153, "stop_count": 130, "is_hub": True},
        {"code": "GZB", "name": "GHAZIABAD JN", "zone": "NR", "state": "Uttar Pradesh", "lat": 28.6679, "lon": 77.4332, "stop_count": 140, "is_hub": True},
        {"code": "AGC", "name": "AGRA CANTT", "zone": "NCR", "state": "Uttar Pradesh", "lat": 27.1587, "lon": 78.0081, "stop_count": 150, "is_hub": True},
        {"code": "JHS", "name": "JHANSI JN", "zone": "NCR", "state": "Uttar Pradesh", "lat": 25.4484, "lon": 78.5685, "stop_count": 210, "is_hub": True},
        {"code": "BINA", "name": "BINA JN", "zone": "WCR", "state": "Madhya Pradesh", "lat": 24.1751, "lon": 78.1873, "stop_count": 120, "is_hub": True},
        {"code": "ET", "name": "ITARSI JN", "zone": "WCR", "state": "Madhya Pradesh", "lat": 22.6139, "lon": 77.7606, "stop_count": 280, "is_hub": True},
        {"code": "KNW", "name": "KHANDWA JN", "zone": "CR", "state": "Madhya Pradesh", "lat": 21.8284, "lon": 76.3533, "stop_count": 110, "is_hub": True},
        {"code": "BSL", "name": "BHUSAVAL JN", "zone": "CR", "state": "Maharashtra", "lat": 21.0455, "lon": 75.7873, "stop_count": 260, "is_hub": True},
        {"code": "MMR", "name": "MANMAD JN", "zone": "CR", "state": "Maharashtra", "lat": 20.2520, "lon": 74.4370, "stop_count": 200, "is_hub": True},
        {"code": "LTT", "name": "LOKMANYA TILAK TERM", "zone": "CR", "state": "Maharashtra", "lat": 19.0699, "lon": 72.8911, "stop_count": 140, "is_hub": True},
        {"code": "BDTS", "name": "BANDRA TERMINUS", "zone": "WR", "state": "Maharashtra", "lat": 19.0628, "lon": 72.8407, "stop_count": 110, "is_hub": True},
        {"code": "BCT", "name": "MUMBAI CENTRAL", "zone": "WR", "state": "Maharashtra", "lat": 18.9696, "lon": 72.8193, "stop_count": 130, "is_hub": True},
        {"code": "TNA", "name": "THANE", "zone": "CR", "state": "Maharashtra", "lat": 19.1860, "lon": 72.9759, "stop_count": 160, "is_hub": True},
        {"code": "PNVL", "name": "PANVEL", "zone": "CR", "state": "Maharashtra", "lat": 18.9894, "lon": 73.1216, "stop_count": 110, "is_hub": True},
        {"code": "SVJR", "name": "SHIVAJINAGAR", "zone": "CR", "state": "Maharashtra", "lat": 18.5314, "lon": 73.8524, "stop_count": 60, "is_hub": True},
        {"code": "KK", "name": "KHADKI", "zone": "CR", "state": "Maharashtra", "lat": 18.5638, "lon": 73.8340, "stop_count": 40, "is_hub": False},
        {"code": "CCH", "name": "CHINCHWAD", "zone": "CR", "state": "Maharashtra", "lat": 18.6298, "lon": 73.7997, "stop_count": 40, "is_hub": False},
        {"code": "DBA", "name": "DABRA", "zone": "NCR", "state": "Madhya Pradesh", "lat": 25.8856, "lon": 78.3304, "stop_count": 50, "is_hub": False},
        {"code": "MRA", "name": "MORENA", "zone": "NCR", "state": "Madhya Pradesh", "lat": 26.5008, "lon": 77.9972, "stop_count": 60, "is_hub": False},
        {"code": "SDAH", "name": "SEALDAH", "zone": "ER", "state": "West Bengal", "lat": 22.5675, "lon": 88.3712, "stop_count": 210, "is_hub": True},
        {"code": "KOAA", "name": "KOLKATA TERMINAL", "zone": "ER", "state": "West Bengal", "lat": 22.6022, "lon": 88.3742, "stop_count": 80, "is_hub": True},
        {"code": "YPR", "name": "YESVANTPUR", "zone": "SWR", "state": "Karnataka", "lat": 13.0238, "lon": 77.5503, "stop_count": 150, "is_hub": True},
        {"code": "SMVB", "name": "SMVT BENGALURU", "zone": "SWR", "state": "Karnataka", "lat": 13.0039, "lon": 77.6534, "stop_count": 90, "is_hub": True},
        {"code": "SC", "name": "SECUNDERABAD", "zone": "SCR", "state": "Telangana", "lat": 17.4344, "lon": 78.5012, "stop_count": 200, "is_hub": True},
        {"code": "RKMP", "name": "RANI KAMALAPATI", "zone": "WCR", "state": "Madhya Pradesh", "lat": 23.2201, "lon": 77.4388, "stop_count": 110, "is_hub": True},
        {"code": "INDB", "name": "INDORE JN", "zone": "WR", "state": "Madhya Pradesh", "lat": 22.7177, "lon": 75.8682, "stop_count": 90, "is_hub": True},
        {"code": "JBP", "name": "JABALPUR JN", "zone": "WCR", "state": "Madhya Pradesh", "lat": 23.1815, "lon": 79.9414, "stop_count": 130, "is_hub": True},
        {"code": "PRYJ", "name": "PRAYAGRAJ JN", "zone": "NCR", "state": "Uttar Pradesh", "lat": 25.4437, "lon": 81.8258, "stop_count": 230, "is_hub": True},
        {"code": "DDU", "name": "PT DD UPADHYAYA", "zone": "ECR", "state": "Uttar Pradesh", "lat": 25.2818, "lon": 83.1197, "stop_count": 260, "is_hub": True},
        {"code": "LKO", "name": "LUCKNOW CHARBAGH", "zone": "NR", "state": "Uttar Pradesh", "lat": 26.8322, "lon": 80.9197, "stop_count": 180, "is_hub": True},
        {"code": "PNBE", "name": "PATNA JN", "zone": "ECR", "state": "Bihar", "lat": 25.6022, "lon": 85.1376, "stop_count": 190, "is_hub": True},
        {"code": "ADI", "name": "AHMEDABAD JN", "zone": "WR", "state": "Gujarat", "lat": 23.0225, "lon": 72.6015, "stop_count": 190, "is_hub": True},
        {"code": "JP", "name": "JAIPUR JN", "zone": "NWR", "state": "Rajasthan", "lat": 26.9196, "lon": 75.7878, "stop_count": 150, "is_hub": True},
        {"code": "ST", "name": "SURAT", "zone": "WR", "state": "Gujarat", "lat": 21.2052, "lon": 72.8407, "stop_count": 170, "is_hub": True},
        {"code": "BRC", "name": "VADODARA JN", "zone": "WR", "state": "Gujarat", "lat": 22.3107, "lon": 73.1812, "stop_count": 210, "is_hub": True},
        {"code": "NGP", "name": "NAGPUR JN", "zone": "CR", "state": "Maharashtra", "lat": 21.1524, "lon": 79.0888, "stop_count": 210, "is_hub": True},
        {"code": "ASR", "name": "AMRITSAR JN", "zone": "NR", "state": "Punjab", "lat": 31.6330, "lon": 74.8656, "stop_count": 80, "is_hub": True},
        {"code": "CDG", "name": "CHANDIGARH", "zone": "NR", "state": "Chandigarh", "lat": 30.7022, "lon": 76.8203, "stop_count": 70, "is_hub": True},
        {"code": "SNSI", "name": "SAINAGAR SHIRDI", "zone": "CR", "state": "Maharashtra", "lat": 19.7645, "lon": 74.4762, "stop_count": 30, "is_hub": True},
        {"code": "SVDK", "name": "SHRI MATA VAISHNO DEVI KATRA", "zone": "NR", "state": "Jammu and Kashmir", "lat": 32.9912, "lon": 74.9317, "stop_count": 40, "is_hub": True},
        {"code": "JAT", "name": "JAMMU TAWI", "zone": "NR", "state": "Jammu and Kashmir", "lat": 32.7063, "lon": 74.8797, "stop_count": 70, "is_hub": True},
        {"code": "UBL", "name": "SSS HUBBALLI JN", "zone": "SWR", "state": "Karnataka", "lat": 15.3496, "lon": 75.1481, "stop_count": 90, "is_hub": True},
        {"code": "MAQ", "name": "MANGALURU CENTRAL", "zone": "SR", "state": "Karnataka", "lat": 12.8631, "lon": 74.8431, "stop_count": 60, "is_hub": True},
        {"code": "TATA", "name": "TATANAGAR JN", "zone": "SER", "state": "Jharkhand", "lat": 22.7667, "lon": 86.2008, "stop_count": 110, "is_hub": True},
        {"code": "UMB", "name": "AMBALA CANTT", "zone": "NR", "state": "Haryana", "lat": 30.3444, "lon": 76.8375, "stop_count": 180, "is_hub": True},
        {"code": "GGN", "name": "GURGAON", "zone": "NR", "state": "Haryana", "lat": 28.4682, "lon": 77.0191, "stop_count": 50, "is_hub": False},
    ]

    cache = []
    by_code = {}
    for item in fallback_stations:
        cache.append(item)
        by_code[item["code"]] = item

    _STATIONS_CACHE = cache
    _STATIONS_BY_CODE = by_code


async def search_stations(query: str, limit: int = 15) -> List[StationSearchResult]:
    """
    Search stations by code prefix, exact code, station name, or city.
    Yields sorted results matching IRCTC autocomplete behavior with active-station prioritization.
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

    # 2. Check if query is an alias (e.g. CSMT -> CSTM, IND -> INDB, JBP -> JBP)
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

    scored: List[tuple[int, int, int, str, str, Dict[str, Any]]] = []

    for s in _STATIONS_CACHE:
        code = s["code"]
        name = s["name"]
        stop_cnt = s.get("stop_count", 0)
        score = 0

        # Exact code match (e.g. 'GWL' == 'GWL', 'JBP' == 'JBP', 'INDB' == 'INDB')
        if code == q_upper:
            score += 3000
        # Alias match (e.g. user typed 'CSMT', station code is 'CSTM')
        elif alias_target and code == alias_target:
            score += 2800
        # Code prefix match (e.g. 'ND' -> 'NDLS')
        elif code.startswith(q_upper):
            score += 1000
        # Code contains query
        elif q_upper in code:
            score += 300

        # Station name checks
        if name == q_upper:
            score += 2200
        elif name.startswith(q_upper):
            score += 850
        elif any(w.startswith(q_upper) for w in name.split()):
            # Word starts with query, e.g. "DELHI" in "NEW DELHI"
            score += 650
        elif q_upper in name:
            score += 250

        # Hub priority boost if city matches
        if code in boosted_hub_ranks:
            rank = boosted_hub_ranks[code]
            score += max(250, 1200 - rank * 80)
        elif s.get("is_hub", False) and (q_upper in name or q_upper in code):
            score += 200

        # ONLY add active/inactive adjustment if the station actually matched the query!
        if score > 0:
            if stop_cnt > 0:
                score += 700 + min(stop_cnt, 500)
            else:
                score -= 400

            # Sort tuple: (-score, -stop_cnt, length of name, name, code, dict)
            scored.append((-score, -stop_cnt, len(name), name, s.get("code", ""), s))

    # If active stations matched, filter out 0-stop inactive stations unless exact code match
    has_active_matches = any(item[5].get("stop_count", 0) > 0 for item in scored)
    if has_active_matches:
        scored = [
            item for item in scored 
            if item[5].get("stop_count", 0) > 0 or item[5]["code"] == q_upper or (alias_target and item[5]["code"] == alias_target)
        ]

    scored.sort()

    results: List[StationSearchResult] = []
    seen_codes = set()

    for item in scored[:limit]:
        s = item[5]
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
