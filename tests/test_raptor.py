"""
Unit tests for the RAPTOR algorithm.
"""

from app.core.raptor import RaptorRouter, time_to_minutes, minutes_to_time_str


def test_time_conversions():
    assert time_to_minutes("07:30:00") == 450
    assert minutes_to_time_str(450) == "07:30"
    assert minutes_to_time_str(1500) == "01:00 (+1d)"


def test_raptor_direct_trip():
    # Train 1: Gwalior -> Bhopal -> Pune
    mock_timetable = [
        {"train_number": "1001", "train_name": "Express 1", "station_code": "GWL", "departure": "06:00", "arrival": None, "day": 1, "stop_sequence": 1},
        {"train_number": "1001", "train_name": "Express 1", "station_code": "BPL", "departure": "12:00", "arrival": "11:30", "day": 1, "stop_sequence": 2},
        {"train_number": "1001", "train_name": "Express 1", "station_code": "PUNE", "departure": None, "arrival": "20:00", "day": 1, "stop_sequence": 3},
    ]

    router = RaptorRouter(mock_timetable)
    journeys = router.plan(origin="GWL", destination="PUNE", max_transfers=1)

    assert len(journeys) >= 1
    direct = [j for j in journeys if j["transfers"] == 0]
    assert len(direct) == 1
    assert direct[0]["legs"][0]["train_number"] == "1001"
    assert direct[0]["legs"][0]["alight_station"] == "PUNE"


def test_raptor_transfer_trip():
    # Train 1: GWL -> BPL (dep 06:00, arr 11:30)
    # Train 2: BPL -> PUNE (dep 13:00, arr 21:00) -> 1.5h changeover at BPL
    mock_timetable = [
        {"train_number": "2001", "train_name": "Leg 1 Train", "station_code": "GWL", "departure": "06:00", "arrival": None, "day": 1, "stop_sequence": 1},
        {"train_number": "2001", "train_name": "Leg 1 Train", "station_code": "BPL", "departure": None, "arrival": "11:30", "day": 1, "stop_sequence": 2},
        {"train_number": "2002", "train_name": "Leg 2 Train", "station_code": "BPL", "departure": "13:00", "arrival": None, "day": 1, "stop_sequence": 1},
        {"train_number": "2002", "train_name": "Leg 2 Train", "station_code": "PUNE", "departure": None, "arrival": "21:00", "day": 1, "stop_sequence": 2},
    ]

    router = RaptorRouter(mock_timetable)
    journeys = router.plan(origin="GWL", destination="PUNE", max_transfers=1, base_transfer_buffer_min=30)

    assert len(journeys) >= 1
    one_transfer = [j for j in journeys if j["transfers"] == 1]
    assert len(one_transfer) == 1
    assert len(one_transfer[0]["legs"]) == 2
    assert one_transfer[0]["legs"][0]["train_number"] == "2001"
    assert one_transfer[0]["legs"][1]["train_number"] == "2002"
