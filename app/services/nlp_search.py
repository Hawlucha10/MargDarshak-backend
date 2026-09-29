"""
Natural Language Search Engine (NLP / Multilingual)
Extracts structured route query parameters from conversational English, Hindi, and Hinglish prompts.
Supports:
  - 200+ city aliases (English, Hindi, Hinglish)
  - Date parsing: "2 oct 2026", "tomorrow", "kal", "parso", "agle hafte", "next Monday"
  - Deadline extraction: "before 11:30", "11:30 se pehle", "subah 11 baje tak"
  - Comfort intent: "ghar se late nikle", "minimize layover"
  - Bus preference: "bus bhi theek hai", "include buses"
"""

import re
from datetime import datetime, date, timedelta
from typing import Dict, Any, Optional
from app.schemas.route import RouteSearchRequest


# ---- 200+ STATION ALIAS MAP ----
STATION_ALIAS_MAP = {
    # English names -> IRCTC codes
    "gwalior": "GWL", "pune": "PUNE", "bhopal": "BPL", "delhi": "NDLS",
    "new delhi": "NDLS", "mumbai": "CSTM", "bombay": "CSTM", "mumbai central": "BCT",
    "jhansi": "JHS", "nagpur": "NGP", "jaipur": "JP", "lucknow": "LKO",
    "kanpur": "CNB", "kolkata": "HWH", "calcutta": "HWH", "bengaluru": "SBC",
    "bangalore": "SBC", "chennai": "MAS", "madras": "MAS", "hyderabad": "SC",
    "secunderabad": "SC", "agra": "AGC", "varanasi": "BSB", "patna": "PNBE",
    "ahmedabad": "ADI", "indore": "INDB", "jabalpur": "JBP", "udaipur": "UDZ",
    "jodhpur": "JU", "ajmer": "AII", "bikaner": "BKN", "kota": "KOTA",
    "surat": "ST", "vadodara": "BRC", "baroda": "BRC", "rajkot": "RJT",
    "mysore": "MYS", "mysuru": "MYS", "coimbatore": "CBE", "madurai": "MDU",
    "trivandrum": "TVC", "ernakulam": "ERS", "kochi": "ERS", "calicut": "CLT",
    "kozhikode": "CLT", "mangalore": "MAQ", "visakhapatnam": "VSKP", "vizag": "VSKP",
    "vijayawada": "BZA", "guntur": "GNT", "tirupati": "TPT",
    "ranchi": "RNC", "dhanbad": "DHN", "allahabad": "PRYJ", "prayagraj": "PRYJ",
    "gorakhpur": "GKP", "mathura": "MTJ", "bareilly": "BE", "aligarh": "APTS",
    "meerut": "MTC", "amritsar": "ASR", "chandigarh": "CDG", "dehradun": "DDN",
    "haridwar": "HW", "jammu": "JAT", "guwahati": "GHY",
    "bhubaneswar": "BBS", "puri": "PURI", "cuttack": "CTC", "rourkela": "ROU",
    "goa": "MAO", "panaji": "KRMI", "nasik": "NK",
    "aurangabad": "AWB", "solapur": "SUR", "kolhapur": "KOP",
    "raipur": "R", "bilaspur": "BSP", "thiruvananthapuram": "TVC",
    "thrissur": "TCR", "howrah": "HWH", "sealdah": "SDAH",
    "new jalpaiguri": "NJP", "siliguri": "NJP", "malda": "MLDT",
    "asansol": "ASN", "durgapur": "DGR", "tatanagar": "TATA",
    "jamshedpur": "TATA", "bokaro": "BKSC", "gaya": "GAYA",
    "muzaffarpur": "MFP", "darbhanga": "DBG",
    "lonavala": "LNL", "panvel": "PNVL", "thane": "TNA",
    "anand vihar": "ANVT", "hazrat nizamuddin": "NZM", "old delhi": "DLI",
    "dadar": "DDR", "kurla": "CLA", "borivali": "BVI",

    # Hinglish / transliterated aliases
    "dilli": "NDLS", "nai dilli": "NDLS", "bambai": "CSTM",
    "kanpur central": "CNB", "banarasi": "BSB", "kashi": "BSB",
    "gwaliar": "GWL", "lucknow junction": "LKO", "allahabad junction": "PRYJ",
    "kolkatta": "HWH", "calcuta": "HWH", "banglore": "SBC",
    "hyderbad": "SC", "secundrabad": "SC", "bhopaL": "BPL",
    "sbc": "SBC", "ndls": "NDLS", "bct": "BCT",

    # Hindi (Devanagari)
    "\u0917\u094d\u0935\u093e\u0932\u093f\u092f\u0930": "GWL",
    "\u092a\u0941\u0923\u0947": "PUNE",
    "\u092d\u094b\u092a\u093e\u0932": "BPL",
    "\u0926\u093f\u0932\u094d\u0932\u0940": "NDLS",
    "\u0928\u0908 \u0926\u093f\u0932\u094d\u0932\u0940": "NDLS",
    "\u092e\u0941\u0902\u092c\u0908": "CSTM",
    "\u091d\u093e\u0902\u0938\u0940": "JHS",
    "\u0928\u093e\u0917\u092a\u0941\u0930": "NGP",
    "\u091c\u092f\u092a\u0941\u0930": "JP",
    "\u0932\u0916\u0928\u0908": "LKO",
    "\u0915\u093e\u0928\u092a\u0941\u0930": "CNB",
    "\u0915\u094b\u0932\u0915\u093e\u0924\u093e": "HWH",
    "\u092c\u0947\u0902\u0917\u0932\u0941\u0930\u0941": "SBC",
    "\u091a\u0947\u0928\u094d\u0928\u0908": "MAS",
    "\u0939\u0948\u0926\u0930\u093e\u092c\u093e\u0926": "SC",
    "\u0906\u0917\u0930\u093e": "AGC",
    "\u0935\u093e\u0930\u093e\u0923\u0938\u0940": "BSB",
    "\u092a\u091f\u0928\u093e": "PNBE",
    "\u0907\u0902\u0926\u094c\u0930": "INDB",
    "\u091c\u092c\u0932\u092a\u0941\u0930": "JBP",
    "\u0909\u0926\u092f\u092a\u0941\u0930": "UDZ",
    "\u0905\u0939\u092e\u0926\u093e\u092c\u093e\u0926": "ADI",
    "\u0938\u0942\u0930\u0924": "ST",
    "\u0935\u0921\u094b\u0926\u0930\u093e": "BRC",
    "\u0930\u093e\u091c\u0915\u094b\u091f": "RJT",
    "\u0915\u094b\u092f\u092e\u094d\u092c\u091f\u0942\u0930": "CBE",
    "\u092e\u0926\u0941\u0930\u0908": "MDU",
    "\u092e\u0948\u0938\u0942\u0930": "MYS",
    "\u0930\u093e\u0901\u091a\u0940": "RNC",
    "\u0917\u094b\u0930\u0916\u092a\u0941\u0930": "GKP",
    "\u092a\u094d\u0930\u092f\u093e\u0917\u0930\u093e\u091c": "PRYJ",
    "\u0905\u092e\u0943\u0924\u0938\u0930": "ASR",
    "\u091a\u0902\u0921\u0940\u0917\u0922\u093c": "CDG",
    "\u0926\u0947\u0939\u0930\u093e\u0926\u0942\u0928": "DDN",
    "\u0939\u0930\u093f\u0926\u094d\u0935\u093e\u0930": "HW",
    "\u0917\u0941\u0935\u093e\u0939\u093e\u091f\u0940": "GHY",
    "\u092d\u0941\u0935\u0928\u0947\u0936\u094d\u0935\u0930": "BBS",
}

# ---- DAY NAMES FOR DATE PARSING ----
DAY_NAMES = {
    "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
    "friday": 4, "saturday": 5, "sunday": 6,
    "mon": 0, "tue": 1, "wed": 2, "thu": 3, "fri": 4, "sat": 5, "sun": 6,
    "somvar": 0, "mangalvar": 1, "budhvar": 2, "guruvar": 3,
    "shukravar": 4, "shanivar": 5, "ravivar": 6,
}

MONTH_NAMES = {
    "jan": 1, "january": 1, "feb": 2, "february": 2, "mar": 3, "march": 3,
    "apr": 4, "april": 4, "may": 5, "jun": 6, "june": 6,
    "jul": 7, "july": 7, "aug": 8, "august": 8, "sep": 9, "september": 9,
    "oct": 10, "october": 10, "nov": 11, "november": 11, "dec": 12, "december": 12,
}


def _parse_date(q: str, today: date) -> date:
    """Parse travel date from natural language."""
    ql = q.lower()

    # Exact date: "2 oct 2026", "2/10/2026", "2-10-2026", "02 october"
    exact_match = re.search(r"(\d{1,2})\s*(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\w*\s*(\d{4})?", ql)
    if exact_match:
        day = int(exact_match.group(1))
        month = MONTH_NAMES.get(exact_match.group(2)[:3], today.month)
        year = int(exact_match.group(3)) if exact_match.group(3) else today.year
        try:
            return date(year, month, day)
        except ValueError:
            pass

    # DD/MM/YYYY or DD-MM-YYYY
    slash_match = re.search(r"(\d{1,2})[/\-](\d{1,2})[/\-](\d{4})", ql)
    if slash_match:
        try:
            return date(int(slash_match.group(3)), int(slash_match.group(2)), int(slash_match.group(1)))
        except ValueError:
            pass

    # Relative dates
    if "today" in ql or "\u0906\u091c" in q:
        return today
    if "tomorrow" in ql or ql.strip() == "kal" or "\u0915\u0932" in q:
        return today + timedelta(days=1)
    if "parso" in ql or "parson" in ql or "\u092a\u0930\u0938\u094b\u0902" in q:
        return today + timedelta(days=2)
    if "agle hafte" in ql or "next week" in ql or "\u0905\u0917\u0932\u0947 \u0939\u092b\u094d\u0924\u0947" in q:
        return today + timedelta(days=7)
    if "next weekend" in ql or "\u0905\u0917\u0932\u0947 \u0935\u0940\u0915\u0947\u0902\u0921" in q:
        days_ahead = (5 - today.weekday() + 7) % 7 or 7
        return today + timedelta(days=days_ahead)

    # Named day: "next Monday", "Friday ko"
    for day_name, day_num in DAY_NAMES.items():
        if day_name in ql:
            days_ahead = (day_num - today.weekday() + 7) % 7 or 7
            return today + timedelta(days=days_ahead)

    # Default: tomorrow
    return today + timedelta(days=1)


def _parse_deadline(q: str) -> Optional[str]:
    """Extract deadline time from query like 'before 11:30' or '11:30 se pehle'."""
    ql = q.lower()

    # "before HH:MM", "by HH:MM"
    before_match = re.search(r"(?:before|by|tak|pehle|se pehle)\s*(\d{1,2})[:\.](\d{2})", ql)
    if before_match:
        return f"{int(before_match.group(1)):02d}:{before_match.group(2)}"

    # "HH:MM se pehle" / "HH:MM tak"
    reverse_match = re.search(r"(\d{1,2})[:\.](\d{2})\s*(?:se pehle|tak|before|se pahle|ke pehle)", ql)
    if reverse_match:
        return f"{int(reverse_match.group(1)):02d}:{reverse_match.group(2)}"

    # "subah 11 baje tak" / "11 baje se pehle" / "raat 10 baje tak"
    baje_match = re.search(r"(\d{1,2})\s*baje\s*(?:tak|se pehle|ke pehle)?", ql)
    if baje_match:
        hour = int(baje_match.group(1))
        # Time of day context
        if "shaam" in ql or "evening" in ql or "\u0936\u093e\u092e" in q:
            hour = hour + 12 if hour < 12 else hour
        elif "raat" in ql or "night" in ql or "\u0930\u093e\u0924" in q:
            hour = hour + 12 if hour < 12 else hour
        return f"{hour:02d}:00"

    # "HH baje" without qualifier
    simple_baje = re.search(r"(\d{1,2})\s*baje", ql)
    if simple_baje:
        return f"{int(simple_baje.group(1)):02d}:00"

    return None


def parse_natural_language_query(query: str) -> Dict[str, Any]:
    """
    Parses a conversational English/Hindi/Hinglish query string into structured routing parameters.
    """
    q = query.strip()
    ql = q.lower()
    today = date.today()

    # 1. Resolve Origin and Destination
    detected_origin: Optional[str] = None
    detected_dest: Optional[str] = None

    # "from X to Y"
    from_to_match = re.search(r"from\s+([a-zA-Z\s]+?)\s+to\s+([a-zA-Z\s]+?)(?:\s+on|\s+by|\s+before|\s*$)", ql)
    if from_to_match:
        cand_orig = from_to_match.group(1).strip().rstrip()
        cand_dest = from_to_match.group(2).strip().rstrip()
        detected_origin = STATION_ALIAS_MAP.get(cand_orig)
        detected_dest = STATION_ALIAS_MAP.get(cand_dest)

    # "X se Y" / "X to Y" (Hinglish)
    if not detected_origin or not detected_dest:
        se_match = re.search(r"([a-zA-Z\u0900-\u097F]+)\s+(?:se|to)\s+([a-zA-Z\u0900-\u097F]+)", ql)
        if se_match:
            c1 = se_match.group(1).strip()
            c2 = se_match.group(2).strip()
            o = STATION_ALIAS_MAP.get(c1, STATION_ALIAS_MAP.get(c1.lower()))
            d = STATION_ALIAS_MAP.get(c2, STATION_ALIAS_MAP.get(c2.lower()))
            if o and d:
                detected_origin = o
                detected_dest = d

    # Hindi "X से Y"
    if not detected_origin or not detected_dest:
        hindi_match = re.search(r"([\u0900-\u097F]+)\s+\u0938\u0947\s+([\u0900-\u097F]+)", q)
        if hindi_match:
            detected_origin = STATION_ALIAS_MAP.get(hindi_match.group(1).strip())
            detected_dest = STATION_ALIAS_MAP.get(hindi_match.group(2).strip())

    # Fallback: scan for station names
    if not detected_origin or not detected_dest:
        found = []
        sorted_aliases = sorted(STATION_ALIAS_MAP.keys(), key=len, reverse=True)
        for alias in sorted_aliases:
            if alias in ql and STATION_ALIAS_MAP[alias] not in found:
                found.append(STATION_ALIAS_MAP[alias])
                if len(found) >= 2:
                    break
        if len(found) >= 2:
            detected_origin = detected_origin or found[0]
            detected_dest = detected_dest or found[1]
        elif len(found) == 1:
            if not detected_origin and not detected_dest:
                # Guess whether it's origin or destination based on prepositions
                if any(w in ql for w in ["to", "tak", "jaana", "ke liye", "pahunch"]):
                    detected_dest = found[0]
                else:
                    detected_origin = found[0]

    needs_clarification = False
    clarification_msg = None

    if not detected_origin and not detected_dest:
        needs_clarification = True
        clarification_msg = f"I couldn't identify an origin or destination in '{query}'. Could you please specify where you want to travel from and to? (e.g., 'Delhi to Mumbai tomorrow' or 'Pune se Gwalior 2 Oct ko')"
        origin = "UNKNOWN"
        destination = "UNKNOWN"
    elif not detected_origin and detected_dest:
        needs_clarification = True
        clarification_msg = f"Where will you be starting your journey to {detected_dest}? (e.g., 'Pune to {detected_dest}' or 'Mumbai se {detected_dest}')"
        origin = "UNKNOWN"
        destination = detected_dest
    elif detected_origin and not detected_dest:
        needs_clarification = True
        clarification_msg = f"Where would you like to travel from {detected_origin}? (e.g., '{detected_origin} to Gwalior' or '{detected_origin} se Delhi')"
        origin = detected_origin
        destination = "UNKNOWN"
    else:
        origin = detected_origin
        destination = detected_dest

    # 2. Date
    travel_date = _parse_date(q, today)
    travel_date_str = travel_date.strftime("%Y-%m-%d")

    # 3. Deadline
    arrive_before = _parse_deadline(q)

    # 4. Priority
    priority = "balanced"
    if any(w in ql for w in ["cheapest", "cheap", "sasta", "\u0938\u0938\u094d\u0924\u093e", "\u0915\u092e \u0915\u093f\u0930\u093e\u092f\u093e", "\u0915\u092e \u092a\u0948\u0938\u0947"]):
        priority = "cheapest"
    elif any(w in ql for w in ["fastest", "fast", "jaldi", "\u091c\u0932\u094d\u0926\u0940", "\u0915\u092e \u0938\u092e\u092f", "\u0924\u0947\u091c"]):
        priority = "fastest"
    elif any(w in ql for w in ["reliable", "safe", "time pe", "\u0938\u092e\u092f \u092a\u0930", "\u092c\u093f\u0928\u093e \u0932\u0947\u091f"]):
        priority = "reliable"
    elif any(w in ql for w in ["comfort", "comfortable", "aaram", "\u0906\u0930\u093e\u092e"]):
        priority = "comfort"

    # 5. Transfer constraints
    max_transfers = 2
    if any(w in ql for w in ["direct", "no change", "seedhi", "nonstop", "\u0938\u0940\u0927\u0940 \u091f\u094d\u0930\u0947\u0928", "\u090f\u0915 \u0939\u0940 \u091f\u094d\u0930\u0947\u0928"]):
        max_transfers = 0
    elif any(w in ql for w in ["1 change", "1 transfer", "ek transfer"]):
        max_transfers = 1

    # 6. Accessibility
    accessible_only = any(
        w in ql for w in ["wheelchair", "accessible", "pwd", "disabled", "\u0926\u093f\u0935\u094d\u092f\u093e\u0902\u0917", "\u0935\u094d\u0939\u0940\u0932\u091a\u0947\u092f\u0930", "\u0930\u0948\u0902\u092a", "\u0932\u093f\u092b\u094d\u091f"]
    )

    # 7. Comfort preference (home wait)
    prefer_home_wait = any(
        w in ql for w in [
            "ghar se late", "ghar pe wait", "wait at home", "minimize layover",
            "station par kam wait", "kam wait", "home pe ruk",
            "\u0918\u0930 \u092a\u0947 \u0930\u0941\u0915", "\u0918\u0930 \u0938\u0947 \u0932\u0947\u091f", "\u0915\u092e \u0935\u0947\u091f",
        ]
    )

    # 8. Bus preference
    include_buses = True
    if any(w in ql for w in ["no bus", "sirf train", "only train", "\u0938\u093f\u0930\u094d\u092b \u091f\u094d\u0930\u0947\u0928"]):
        include_buses = False
    elif any(w in ql for w in ["bus bhi", "include bus", "bus ok", "bus theek", "bus chalega"]):
        include_buses = True

    request_payload = RouteSearchRequest(
        origin=origin,
        destination=destination,
        travel_date=travel_date_str,
        max_transfers=max_transfers,
        priority=priority,
        accessible_only=accessible_only,
        arrive_before_time=arrive_before,
        prefer_home_wait=prefer_home_wait,
        include_buses=include_buses,
    )

    return {
        "original_query": query,
        "parsed_request": request_payload,
        "needs_clarification": needs_clarification,
        "clarification_message": clarification_msg,
        "extracted_entities": {
            "origin_station": origin,
            "destination_station": destination,
            "travel_date": travel_date_str,
            "priority": priority,
            "max_transfers": max_transfers,
            "accessible_only": accessible_only,
            "arrive_before_time": arrive_before,
            "prefer_home_wait": prefer_home_wait,
            "include_buses": include_buses,
            "needs_clarification": needs_clarification,
            "clarification_message": clarification_msg,
        },
    }
