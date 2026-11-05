"""Warehouse routing with shortest-path distance calculation."""

import heapq
import math
from collections.abc import Mapping

type WarehouseGraph = dict[str, dict[str, float]]


def shortest_distance(
    graph: Mapping[str, Mapping[str, float]],
    start: str,
    destination: str,
) -> float | None:
    """Find the shortest route using Dijkstra's algorithm.

    Return None when a station is unknown or unreachable.
    """
    if not start or not destination:
        return None

    for station, neighbors in graph.items():
        for neighbor, weight in neighbors.items():
            if neighbor not in graph or not math.isfinite(weight) or weight < 0:
                raise ValueError(f"Invalid connection: {station} -> {neighbor}")

    if start not in graph or destination not in graph:
        return None

    distances = {start: 0.0}
    queue = [(0.0, start)]

    while queue:
        current_distance, station = heapq.heappop(queue)

        if current_distance > distances[station]:
            continue

        if station == destination:
            return current_distance

        for neighbor, weight in graph[station].items():
            candidate = current_distance + weight

            if candidate < distances.get(neighbor, math.inf):
                distances[neighbor] = candidate
                heapq.heappush(queue, (candidate, neighbor))

    return None


def build_demo_warehouse() -> WarehouseGraph:
    """Return a sample, bidirectional warehouse layout."""
    graph: WarehouseGraph = {
        station: {}
        for station in (
            "STATION-A1",
            "STATION-A2",
            "STATION-A3",
            "STATION-B1",
            "STATION-B2",
            "STATION-B3",
        )
    }

    connections = (
        ("STATION-A1", "STATION-A2", 10.0),
        ("STATION-A2", "STATION-A3", 10.0),
        ("STATION-B1", "STATION-B2", 10.0),
        ("STATION-B2", "STATION-B3", 10.0),
        ("STATION-A1", "STATION-B1", 8.0),
        ("STATION-A2", "STATION-B2", 8.0),
        ("STATION-A3", "STATION-B3", 8.0),
    )

    for start, end, distance in connections:
        graph[start][end] = distance
        graph[end][start] = distance

    return graph
