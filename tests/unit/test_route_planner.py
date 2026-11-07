"""Tests for energy-aware route planning."""

from apps.backend.services.route_planner import (
    calculate_plan,
    shortest_path,
)
from apps.backend.services.warehouse_graph import (
    build_demo_warehouse,
)


def test_shortest_path_uses_connected_aisles():
    graph = build_demo_warehouse()

    result = shortest_path(
        graph,
        "STATION-A1",
        "STATION-B2",
    )

    assert result is not None
    path, distance = result

    assert path[0] == "STATION-A1"
    assert path[-1] == "STATION-B2"
    assert distance == 14.0


def test_plan_calculates_whole_mission_energy():
    graph = build_demo_warehouse()

    plan = calculate_plan(
        graph,
        "STATION-A1",
        "STATION-A2",
        "STATION-B3",
        battery=80,
    )

    assert plan is not None
    assert plan["total_distance"] == 20.0
    assert plan["energy_required"] == 7.0
    assert plan["battery_after"] == 73.0
    assert plan["feasible"] is True
    assert plan["path"][0] == "STATION-A1"
    assert plan["path"][-1] == "STATION-B3"


def test_insufficient_battery_is_rejected():
    graph = build_demo_warehouse()

    plan = calculate_plan(
        graph,
        "STATION-A1",
        "STATION-A2",
        "STATION-B3",
        battery=25,
    )

    assert plan is not None
    assert plan["feasible"] is False
