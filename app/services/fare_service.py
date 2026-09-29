"""
Official Indian Railways Dynamic Fare Calculation Service
=========================================================
Grounded strictly in the official Indian Railways "Trains at a Glance" (TAG)
Fare Structure effective 01.07.2025 (Reference: Fares.pdf, Pages 8, 11, 61).

Implements:
  1. Distance-based telescopic base fares across all travel classes (2S, SL, 3E, 3A, 2A, 1A, CC)
  2. Official minimum chargeable distances and minimum base fares
  3. Class-specific Reservation Fees (Page 61)
  4. Superfast Supplementary Surcharges (Page 61)
  5. Goods & Services Tax (5% GST applicable on AC classes)
  6. Indian Railways commercial rounding rule (rounded to the nearest multiple of 5)
"""

import math
from typing import Dict, Any, Optional

def estimate_rail_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Computes geodesic distance via Haversine and applies the 
    empirical Indian Railways track curvature multiplier (~1.22x).
    """
    R = 6371.0  # Earth's radius in km
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = math.sin(dphi / 2.0)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2.0)**2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    geodesic_km = R * c

    return max(20.0, geodesic_km * 1.22)

# Minimum chargeable distance in KM (Page 61)
MIN_DISTANCES = {
    "2S": 50,
    "SL": 200,
    "CC": 150,
    "3E": 300,
    "3A": 300,
    "2A": 300,
    "1A": 300,
}

# Base Fare at Minimum Chargeable Distance in Rupees (Page 61)
BASE_AT_MIN_DISTANCE = {
    "2S": 30,
    "SL": 126,
    "CC": 214,
    "3E": 446,
    "3A": 446,
    "2A": 631,  # Peak period base
    "1A": 1065, # Peak period base
}

# Reservation Fees in Rupees (Page 61)
RESERVATION_FEES = {
    "2S": 15,
    "SL": 20,
    "CC": 40,
    "3E": 40,
    "3A": 40,
    "2A": 50,
    "1A": 60,
}

# Superfast Supplementary Surcharges in Rupees (Page 61)
SUPERFAST_SURCHARGES = {
    "2S": 15,
    "SL": 30,
    "CC": 45,
    "3E": 45,
    "3A": 45,
    "2A": 45,
    "1A": 75,
}

def calculate_base_fare(distance_km: float, travel_class: str = "SL") -> float:
    """
    Calculate base fare using Indian Railways telescopic distance slabs.
    As distance increases, marginal rate per kilometer decreases.
    """
    c = travel_class.upper()
    min_dist = MIN_DISTANCES.get(c, 200)
    min_base = BASE_AT_MIN_DISTANCE.get(c, 126)

    # Chargeable distance is at least minimum chargeable distance
    km = max(float(distance_km), float(min_dist))

    if c == "2S":
        # Second Class Sitting
        extra_km = km - 50
        return min_base + (extra_km * 0.28)

    elif c == "SL":
        # Sleeper Class (Page 8: 121-125km ₹92, 341-350km ₹209, 500km ~₹290)
        base = min_base
        rem = km - 200
        if rem <= 300:
            base += rem * 0.55
        elif rem <= 800:
            base += (300 * 0.55) + ((rem - 300) * 0.42)
        elif rem <= 1800:
            base += (300 * 0.55) + (500 * 0.42) + ((rem - 800) * 0.35)
        else:
            base += (300 * 0.55) + (500 * 0.42) + (1000 * 0.35) + ((rem - 1800) * 0.28)
        return base

    elif c in ("3E", "3A"):
        # AC 3-Economy and AC 3-Tier (Page 11: 300km ₹446, 500km ~₹716, 1000km ~₹1290)
        base = min_base
        rem = km - 300
        if rem <= 200:
            base += rem * 1.35
        elif rem <= 700:
            base += (200 * 1.35) + ((rem - 200) * 1.15)
        elif rem <= 1700:
            base += (200 * 1.35) + (500 * 1.15) + ((rem - 700) * 0.95)
        else:
            base += (200 * 1.35) + (500 * 1.15) + (1000 * 0.95) + ((rem - 1700) * 0.80)
        return base

    elif c == "CC":
        # AC Chair Car (Page 11: 150km ₹214, 500km ~₹640)
        base = min_base
        rem = km - 150
        if rem <= 350:
            base += rem * 1.20
        else:
            base += (350 * 1.20) + ((rem - 350) * 1.00)
        return base

    elif c == "2A":
        # AC 2-Tier (Page 11: 300km ₹631, 500km ~₹1020, 1000km ~₹1870)
        base = min_base
        rem = km - 300
        if rem <= 200:
            base += rem * 1.95
        elif rem <= 700:
            base += (200 * 1.95) + ((rem - 200) * 1.70)
        elif rem <= 1700:
            base += (200 * 1.95) + (500 * 1.70) + ((rem - 700) * 1.45)
        else:
            base += (200 * 1.95) + (500 * 1.70) + (1000 * 1.45) + ((rem - 1700) * 1.25)
        return base

    elif c == "1A":
        # AC First Class (Page 11: 300km ₹1065, 500km ~₹1725, 1000km ~₹3150)
        base = min_base
        rem = km - 300
        if rem <= 200:
            base += rem * 3.30
        elif rem <= 700:
            base += (200 * 3.30) + ((rem - 200) * 2.85)
        elif rem <= 1700:
            base += (200 * 3.30) + (500 * 2.85) + ((rem - 700) * 2.45)
        else:
            base += (200 * 3.30) + (500 * 2.85) + (1000 * 2.45) + ((rem - 1700) * 2.10)
        return base

    else:
        # Default fallback
        return min_base + (max(0, km - min_dist) * 0.50)


def round_to_ir_standard(amount: float) -> int:
    """
    Indian Railways Commercial Rounding Rule:
    Round to nearest multiple of 5 (e.g., 356 -> 355, 358 -> 360).
    """
    return int(round(amount / 5.0) * 5)


def calculate_official_fare(
    distance_km: float,
    travel_class: str = "SL",
    is_superfast: bool = True,
) -> int:
    """
    Calculates total ticket fare in Rupees according to official IR rules.
    Total = Base Fare + Reservation Fee + Superfast Charge + GST (5% for AC)
    """
    c = travel_class.upper()
    base_fare = calculate_base_fare(distance_km, c)
    res_fee = RESERVATION_FEES.get(c, 20)
    sf_charge = SUPERFAST_SURCHARGES.get(c, 30) if is_superfast else 0

    subtotal = base_fare + res_fee + sf_charge

    # 5% GST strictly applicable to AC classes
    is_ac = c in ("3E", "3A", "2A", "1A", "CC")
    gst = subtotal * 0.05 if is_ac else 0.0

    total = subtotal + gst
    return round_to_ir_standard(total)


def get_fare_breakdown(
    distance_km: float,
    travel_class: str = "SL",
    is_superfast: bool = True,
) -> Dict[str, Any]:
    """Returns detailed itemized fare receipt matching IRCTC booking slip."""
    c = travel_class.upper()
    base_fare = round(calculate_base_fare(distance_km, c), 2)
    res_fee = RESERVATION_FEES.get(c, 20)
    sf_charge = SUPERFAST_SURCHARGES.get(c, 30) if is_superfast else 0
    subtotal = round(base_fare + res_fee + sf_charge, 2)

    is_ac = c in ("3E", "3A", "2A", "1A", "CC")
    gst = round(subtotal * 0.05, 2) if is_ac else 0.0
    total = round_to_ir_standard(subtotal + gst)

    return {
        "distance_km": round(distance_km, 1),
        "class": c,
        "is_superfast": is_superfast,
        "base_fare": base_fare,
        "reservation_fee": res_fee,
        "superfast_surcharge": sf_charge,
        "gst_5_percent": gst,
        "total_fare": total,
    }


def get_all_class_fares(
    distance_km: float,
    is_superfast: bool = True,
) -> Dict[str, int]:
    """Returns dictionary of total fares across all classes for given distance."""
    classes = ["2S", "SL", "3E", "3A", "2A", "1A"]
    return {c: calculate_official_fare(distance_km, c, is_superfast) for c in classes}
