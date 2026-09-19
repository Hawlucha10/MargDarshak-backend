"""
RAPTOR: Round-Based Public Transit Optimized Router
Computes Pareto-optimal journeys across multiple transfer rounds.
"""

from datetime import datetime, time, timedelta
from typing import List, Dict, Any, Optional, Set, Tuple


def time_to_minutes(t: time | str) -> int:
    """Converts a datetime.time or 'HH:MM:SS' string into minutes since midnight."""
    if isinstance(t, str):
        parts = [int(p) for p in t.strip().split(":")]
        return parts[0] * 60 + parts[1]
    return t.hour * 60 + t.minute


def minutes_to_time_str(m: int) -> str:
    """Converts minutes since midnight to HH:MM format (handles overnight journeys > 24h)."""
    days = m // (24 * 60)
    rem = m % (24 * 60)
    hh = rem // 60
    mm = rem % 60
    if days > 0:
        return f"{hh:02d}:{mm:02d} (+{days}d)"
    return f"{hh:02d}:{mm:02d}"


class RaptorRouter:
    """
    RAPTOR router operating over in-memory timetable arrays.
    """

    def __init__(self, timetable_records: List[Dict[str, Any]]):
        """
        Organizes flat timetable records into train routes and station-to-train indices.
        Each record expected to have:
          train_number, train_name, station_code, station_name, arrival, departure, day, stop_sequence
        """
        self.routes: Dict[str, List[Dict[str, Any]]] = {}
        self.station_to_trains: Dict[str, Set[str]] = {}

        # Group by train_number
        for row in timetable_records:
            t_num = str(row["train_number"]).strip()
            st_code = str(row["station_code"]).strip().upper()

            if t_num not in self.routes:
                self.routes[t_num] = []
            self.routes[t_num].append(row)

            if st_code not in self.station_to_trains:
                self.station_to_trains[st_code] = set()
            self.station_to_trains[st_code].add(t_num)

        # Sort each train's stops by day and sequence or arrival time
        for t_num, stops in self.routes.items():
            stops.sort(key=lambda s: (s.get("day", 1), s.get("stop_sequence", 0)))

    def plan(
        self,
        origin: str,
        destination: str,
        start_time_minutes: int = 0,
        max_transfers: int = 2,
        base_transfer_buffer_min: int = 30,
        delay_adjustments: Optional[Dict[Tuple[str, str], int]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Executes RAPTOR rounds up to max_transfers + 1.
        Returns all discovered candidate paths to destination.
        """
        origin = origin.upper()
        destination = destination.upper()
        delay_adjustments = delay_adjustments or {}

        max_rounds = max_transfers + 1
        INF = 10**9

        # earliest_arrival[k][station] = minutes
        earliest_arrival: List[Dict[str, int]] = [{} for _ in range(max_rounds + 1)]
        parent_leg: List[Dict[str, Any]] = [{} for _ in range(max_rounds + 1)]

        for k in range(max_rounds + 1):
            earliest_arrival[k][origin] = start_time_minutes

        marked_stations: Set[str] = {origin}
        found_journeys: List[Dict[str, Any]] = []

        for k in range(1, max_rounds + 1):
            # Copy forward previous round's arrivals
            for st, arr in earliest_arrival[k - 1].items():
                earliest_arrival[k][st] = arr

            next_marked: Set[str] = set()

            # Find all routes passing through any marked station
            candidate_routes: Set[str] = set()
            for st in marked_stations:
                if st in self.station_to_trains:
                    candidate_routes.update(self.station_to_trains[st])

            for t_num in candidate_routes:
                stops = self.routes.get(t_num, [])
                boarded_idx: Optional[int] = None

                for i, stop in enumerate(stops):
                    st = stop["station_code"].upper()

                    # Check if we can board at this stop
                    if boarded_idx is None:
                        if st in marked_stations:
                            prev_arr = earliest_arrival[k - 1].get(st, INF)
                            dep_time_raw = stop.get("departure")
                            if dep_time_raw:
                                # Add base buffer if this is a transfer (round > 1)
                                required_dep = prev_arr + (base_transfer_buffer_min if k > 1 else 0)
                                dep_m = time_to_minutes(dep_time_raw) + (stop.get("day", 1) - 1) * 1440

                                if dep_m >= required_dep:
                                    boarded_idx = i
                    else:
                        # Already on board, check arrival at subsequent stop
                        arr_time_raw = stop.get("arrival")
                        if arr_time_raw:
                            arr_m = time_to_minutes(arr_time_raw) + (stop.get("day", 1) - 1) * 1440

                            # Apply ML delay adjustment if present
                            pred_delay = delay_adjustments.get((t_num, st), 0)
                            effective_arr_m = arr_m + pred_delay

                            current_best = earliest_arrival[k].get(st, INF)
                            if effective_arr_m < current_best:
                                earliest_arrival[k][st] = effective_arr_m
                                parent_leg[k][st] = {
                                    "train_number": t_num,
                                    "train_name": stop.get("train_name", ""),
                                    "board_station": stops[boarded_idx]["station_code"],
                                    "board_station_name": stops[boarded_idx].get("station_name", ""),
                                    "dep_time": stops[boarded_idx].get("departure"),
                                    "dep_minutes": time_to_minutes(stops[boarded_idx].get("departure", "00:00")),
                                    "alight_station": st,
                                    "alight_station_name": stop.get("station_name", ""),
                                    "arr_time": stop.get("arrival"),
                                    "arr_minutes": effective_arr_m,
                                    "predicted_delay": pred_delay,
                                    "day": stop.get("day", 1),
                                }
                                next_marked.add(st)

                                # If reached target destination, record candidate
                                if st == destination:
                                    found_journeys.append({
                                        "round": k,
                                        "transfers": k - 1,
                                        "arrival_minutes": effective_arr_m,
                                        "legs": self._reconstruct_path(parent_leg, k, destination),
                                    })

            marked_stations = next_marked
            if not marked_stations:
                break

        return found_journeys

    def _reconstruct_path(self, parent_leg: List[Dict[str, Any]], target_k: int, destination: str) -> List[Dict[str, Any]]:
        """Reconstructs the full sequence of train legs taken across rounds."""
        legs = []
        curr_st = destination
        curr_k = target_k

        while curr_k > 0 and curr_st in parent_leg[curr_k]:
            leg = parent_leg[curr_k][curr_st]
            legs.append(leg)
            curr_st = leg["board_station"]
            curr_k -= 1

        legs.reverse()
        return legs
