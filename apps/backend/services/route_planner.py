"""Shortest-path planning and demonstration energy estimates."""

import math

import fleet_scheduler

from apps.backend.services.advanced_motion import route_duration
from apps.backend.services.warehouse_graph import WarehouseGraph

# Demonstration assumptions, not hardware-calibrated values.
ENERGY_PERCENT_PER_DISTANCE = 0.35
SAFETY_RESERVE_PERCENT = 20.0
SECONDS_PER_DISTANCE = 0.8
MIN_SIMULATION_SECONDS = 8


def shortest_path(
    graph: WarehouseGraph,
    start: str,
    goal: str,
) -> tuple[list[str], float] | None:
    """Find route using Rust. Preserve the existing Python return shape."""
    if start not in graph or goal not in graph:
        return None
    edges: list[tuple[str, str, float]] = []
    for station, neighbors in graph.items():
        for neighbor, weight in neighbors.items():
            if not math.isfinite(weight) or weight < 0 or neighbor not in graph:
                raise ValueError("Invalid warehouse edge weight.")
            edges.append((station, neighbor, float(weight)))
    return fleet_scheduler.shortest_path(edges, start, goal)

def calculate_plan(
    graph: WarehouseGraph,
    robot_station: str,
    pickup: str,
    delivery: str,
    battery: float,
) -> dict | None:
    """Calculate travel, battery feasibility and simulated duration."""

    to_pickup = shortest_path(graph, robot_station, pickup)
    to_delivery = shortest_path(graph, pickup, delivery)

    if to_pickup is None or to_delivery is None:
        return None

    pickup_path, pickup_distance = to_pickup
    delivery_path, delivery_distance = to_delivery

    route = pickup_path + delivery_path[1:]
    total_distance = pickup_distance + delivery_distance
    energy_required = fleet_scheduler.estimate_energy(
        total_distance, ENERGY_PERCENT_PER_DISTANCE
    )
    estimated_battery_after = round(battery - energy_required, 2)

    feasible = battery >= 30 and estimated_battery_after >= SAFETY_RESERVE_PERCENT

    duration = max(
        MIN_SIMULATION_SECONDS,
        math.ceil(route_duration(route)),
    )

    return {
        "path": route,
        "pickup_path": pickup_path,
        "delivery_path": delivery_path,
        "pickup_distance": pickup_distance,
        "delivery_distance": delivery_distance,
        "total_distance": total_distance,
        "battery_before": battery,
        "energy_required": energy_required,
        "battery_after": estimated_battery_after,
        "safety_reserve": SAFETY_RESERVE_PERCENT,
        "duration_seconds": duration,
        "feasible": feasible,
        "energy_model": "demo_linear_v1",
    }
