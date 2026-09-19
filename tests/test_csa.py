"""
Unit tests for the Connection Scan Algorithm (CSA).
"""

from app.core.csa import Connection, ConnectionScanRouter


def test_csa_basic_path():
    connections = [
        Connection("101", "GWL", "BPL", departure_minutes=360, arrival_minutes=690),  # 06:00 -> 11:30
        Connection("102", "BPL", "PUNE", departure_minutes=750, arrival_minutes=1260), # 12:30 -> 21:00
        Connection("103", "DEL", "MUM", departure_minutes=400, arrival_minutes=900),
    ]

    csa = ConnectionScanRouter(connections)
    res = csa.search_earliest_arrival("GWL", "PUNE", start_time_minutes=300, min_transfer_buffer_min=20)

    assert res is not None
    assert res["earliest_arrival_minutes"] == 1260
    assert len(res["legs"]) == 2
    assert res["legs"][0]["train_number"] == "101"
    assert res["legs"][1]["train_number"] == "102"


def test_csa_live_delay_missed_connection():
    connections = [
        Connection("101", "GWL", "BPL", departure_minutes=360, arrival_minutes=690),  # arr 11:30 (690m)
        Connection("102", "BPL", "PUNE", departure_minutes=710, arrival_minutes=1200), # dep 11:50 (710m) - 20m buffer
        Connection("104", "BPL", "PUNE", departure_minutes=840, arrival_minutes=1350), # dep 14:00 (840m) - fallback train
    ]

    csa = ConnectionScanRouter(connections)
    # Before delay: catches 102
    res_before = csa.search_earliest_arrival("GWL", "PUNE", start_time_minutes=300, min_transfer_buffer_min=15)
    assert res_before["legs"][1]["train_number"] == "102"

    # Live update: Train 101 delayed by 40 minutes (arr at 730m > 710m)
    csa.update_delay("101", delay_minutes=40)

    # After delay: misses 102, automatically catches fallback 104!
    res_after = csa.search_earliest_arrival("GWL", "PUNE", start_time_minutes=300, min_transfer_buffer_min=15)
    assert res_after["legs"][1]["train_number"] == "104"
