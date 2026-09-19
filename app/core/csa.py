"""
Connection Scan Algorithm (CSA)
Ultra-fast timetable linear scan for minimum travel time and real-time delay re-computation.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class Connection:
    train_number: str
    from_station: str
    to_station: str
    departure_minutes: int
    arrival_minutes: int
    day: int = 1


class ConnectionScanRouter:
    """
    Implements CSA over chronologically sorted connections.
    """

    def __init__(self, connections: List[Connection]):
        # Sort strictly by departure_minutes
        self.connections = sorted(connections, key=lambda c: c.departure_minutes)

    def update_delay(self, train_number: str, delay_minutes: int) -> None:
        """
        Applies a live delay update to all matching connections and maintains sorting.
        """
        for c in self.connections:
            if c.train_number == train_number:
                c.departure_minutes += delay_minutes
                c.arrival_minutes += delay_minutes
        # Re-sort
        self.connections.sort(key=lambda c: c.departure_minutes)

    def search_earliest_arrival(
        self,
        origin: str,
        destination: str,
        start_time_minutes: int = 0,
        min_transfer_buffer_min: int = 20,
    ) -> Optional[Dict[str, Any]]:
        """
        Performs a single linear scan from top to bottom.
        Returns earliest arrival and journey sequence.
        """
        origin = origin.upper()
        destination = destination.upper()
        INF = 10**9

        earliest_arrival: Dict[str, int] = {}
        in_connection: Dict[str, Connection] = {}

        earliest_arrival[origin] = start_time_minutes

        for c in self.connections:
            dep_station = c.from_station.upper()
            arr_station = c.to_station.upper()

            # Required arrival at dep_station before we can board
            station_reachable = earliest_arrival.get(dep_station, INF)

            # Check if this is initial boarding or transfer
            buffer = 0 if dep_station == origin else min_transfer_buffer_min

            if c.departure_minutes >= station_reachable + buffer:
                current_dest_arr = earliest_arrival.get(arr_station, INF)
                if c.arrival_minutes < current_dest_arr:
                    earliest_arrival[arr_station] = c.arrival_minutes
                    in_connection[arr_station] = c

        if destination not in earliest_arrival or earliest_arrival[destination] == INF:
            return None

        # Reconstruct journey
        path = []
        curr = destination
        while curr != origin and curr in in_connection:
            conn = in_connection[curr]
            path.append({
                "train_number": conn.train_number,
                "from_station": conn.from_station,
                "to_station": conn.to_station,
                "dep_minutes": conn.departure_minutes,
                "arr_minutes": conn.arrival_minutes,
            })
            curr = conn.from_station

        path.reverse()
        return {
            "origin": origin,
            "destination": destination,
            "earliest_arrival_minutes": earliest_arrival[destination],
            "total_travel_minutes": earliest_arrival[destination] - start_time_minutes,
            "legs": path,
        }
