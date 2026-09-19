"""
Natural Language Search Engine (NLP / Multilingual)
Extracts structured route query parameters from conversational English and Hindi prompts.
Supports city-to-station resolution and natural date parsing.
"""

import re
from datetime import datetime, date, timedelta
from typing import Dict, Any, Optional
from app.schemas.route import RouteSearchRequest


# City / Hindi to IRCTC Station Code Resolver
STATION_ALIAS_MAP = {
    # English names
    "gwalior": "GWL",
    "pune": "PUNE",
    "bhopal": "BPL",
    "delhi": "NDLS",
    "new delhi": "NDLS",
    "mumbai": "CSMT",
    "bombay": "CSMT",
    "jhansi": "JHS",
    "nagpur": "NGP",
    "jaipur": "JP",
    "lucknow": "LKO",
    "kanpur": "CNB",
    "kolkata": "HWH",
    "calcutta": "HWH",
    "bengaluru": "SBC",
    "bangalore": "SBC",
    "chennai": "MAS",
    "madras": "MAS",
    "hyderabad": "SC",
    "secunderabad": "SC",
    "agra": "AGC",
    "varanasi": "BSB",
    "patna": "PNBE",
    "ahmedabad": "ADI",

    # Hindi names (Devanagari)
    "ग्वालियर": "GWL",
    "पुणे": "PUNE",
    "भोपाल": "BPL",
    "दिल्ली": "NDLS",
    "नई दिल्ली": "NDLS",
    "मुंबई": "CSMT",
    "झांसी": "JHS",
    "नागपुर": "NGP",
    "जयपुर": "JP",
    "लखनऊ": "LKO",
    "कानपुर": "CNB",
    "कोलकाता": "HWH",
    "बेंगलुरु": "SBC",
    "चेन्नई": "MAS",
    "हैदराबाद": "SC",
    "आगरा": "AGC",
    "वाराणसी": "BSB",
    "पटना": "PNBE",
}


def parse_natural_language_query(query: str) -> Dict[str, Any]:
    """
    Parses a conversational English/Hindi query string into structured routing parameters.
    """
    q = query.lower().strip()
    today = date.today()

    # 1. Resolve Origin and Destination
    detected_origin: Optional[str] = None
    detected_dest: Optional[str] = None

    # Detect English patterns: "from X to Y"
    from_to_match = re.search(r"from\s+([a-zA-Z\s]+?)\s+to\s+([a-zA-Z\s]+)", q)
    if from_to_match:
        cand_orig = from_to_match.group(1).strip()
        cand_dest = from_to_match.group(2).strip().split()[0]  # first word
        detected_origin = STATION_ALIAS_MAP.get(cand_orig)
        detected_dest = STATION_ALIAS_MAP.get(cand_dest)

    # Detect Hindi patterns: "X से Y"
    if not detected_origin or not detected_dest:
        hindi_match = re.search(r"([^\s]+)\s+से\s+([^\s]+)", query)
        if hindi_match:
            cand_orig = hindi_match.group(1).strip()
            cand_dest = hindi_match.group(2).strip()
            detected_origin = STATION_ALIAS_MAP.get(cand_orig, STATION_ALIAS_MAP.get(cand_orig.lower()))
            detected_dest = STATION_ALIAS_MAP.get(cand_dest, STATION_ALIAS_MAP.get(cand_dest.lower()))

    # Fallback keyword scanning
    if not detected_origin or not detected_dest:
        found_stations = []
        for alias, code in STATION_ALIAS_MAP.items():
            if alias in q:
                if code not in found_stations:
                    found_stations.append(code)
        if len(found_stations) >= 2:
            detected_origin = detected_origin or found_stations[0]
            detected_dest = detected_dest or found_stations[1]

    # Defaults if missing
    origin = detected_origin or "GWL"
    destination = detected_dest or "PUNE"

    # 2. Date extraction
    target_date = today + timedelta(days=1)  # Default tomorrow
    if "today" in q or "आज" in q:
        target_date = today
    elif "tomorrow" in q or "कल" in q:
        target_date = today + timedelta(days=1)
    elif "next weekend" in q or "अगले वीकेंड" in q:
        # Days until next Saturday (weekday 5)
        days_ahead = (5 - today.weekday() + 7) % 7 or 7
        target_date = today + timedelta(days=days_ahead)

    travel_date_str = target_date.strftime("%Y-%m-%d")

    # 3. Priority extraction
    priority = "balanced"
    if any(word in q for word in ["cheapest", "cheap", "सस्ता", "कम किराया", "कम पैसे"]):
        priority = "cheapest"
    elif any(word in q for word in ["fastest", "fast", "जल्दी", "कम समय", "तेज"]):
        priority = "fastest"
    elif any(word in q for word in ["reliable", "safe", "समय पर", "बिना लेट"]):
        priority = "reliable"

    # 4. Transfer constraints
    max_transfers = 2
    if any(word in q for word in ["direct", "no change", "एक ही ट्रेन", "सीधी ट्रेन"]):
        max_transfers = 0
    elif any(word in q for word in ["1 change", "least changes", "1 ट्रांसफर"]):
        max_transfers = 1

    # 5. Accessibility constraint
    accessible_only = any(
        word in q for word in ["wheelchair", "accessible", "pwd", "disabled", "दिव्यांग", "व्हीलचेयर", "रैंप", "लिफ्ट"]
    )

    request_payload = RouteSearchRequest(
        origin=origin,
        destination=destination,
        travel_date=travel_date_str,
        max_transfers=max_transfers,
        priority=priority,
        accessible_only=accessible_only,
    )

    return {
        "original_query": query,
        "parsed_request": request_payload,
        "extracted_entities": {
            "origin_station": origin,
            "destination_station": destination,
            "travel_date": travel_date_str,
            "priority": priority,
            "max_transfers": max_transfers,
            "accessible_only": accessible_only,
        },
    }
