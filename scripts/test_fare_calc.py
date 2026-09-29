import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services.fare_service import get_fare_breakdown, get_all_class_fares

print("=== 900 KM (e.g. NZM to JBP on 22182 Superfast) ===")
print("All Classes:", get_all_class_fares(900, is_superfast=True))
print("Sleeper Breakdown:", get_fare_breakdown(900, "SL", is_superfast=True))
print("3AC Breakdown:", get_fare_breakdown(900, "3A", is_superfast=True))

print("\n=== 1200 KM (e.g. GWL to PUNE) ===")
print("All Classes:", get_all_class_fares(1200, is_superfast=True))
print("Sleeper Breakdown:", get_fare_breakdown(1200, "SL", is_superfast=True))
print("3AC Breakdown:", get_fare_breakdown(1200, "3A", is_superfast=True))
