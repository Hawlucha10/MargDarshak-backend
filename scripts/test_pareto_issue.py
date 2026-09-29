import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.pareto import assign_pareto_labels

sample = [
    {"travel_time_min": 600, "fare": 500, "transfers": 0, "wait_time_min": 0, "reliability": 0.9}
]

try:
    assign_pareto_labels(sample)
    print("SUCCESS")
except Exception as e:
    print("CRASHED WITH:", type(e), e)
