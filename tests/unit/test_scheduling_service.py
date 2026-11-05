"""Tests for Python and Rust scheduling integration."""

from apps.backend.models.robot import Robot, RobotStatus
from apps.backend.services.scheduling_service import recommend_robot
from apps.backend.services.warehouse_graph import build_demo_warehouse


def make_robot(name, location, battery, status):
    return Robot(
        name=name,
        current_location=location,
        battery_level=battery,
        status=status,
    )


def test_selects_nearest_robot():
    robots = [
        make_robot("AMR-001", "STATION-A1", 80, RobotStatus.AVAILABLE),
        make_robot("AMR-002", "STATION-B2", 70, RobotStatus.AVAILABLE),
    ]

    selected = recommend_robot(
        robots,
        "STATION-B3",
        build_demo_warehouse(),
    )

    assert selected == str(robots[1].id)


def test_excludes_offline_robots():
    robots = [
        make_robot("AMR-001", "STATION-B3", 90, RobotStatus.OFFLINE),
        make_robot("AMR-002", "STATION-A3", 60, RobotStatus.AVAILABLE),
    ]

    selected = recommend_robot(
        robots,
        "STATION-B3",
        build_demo_warehouse(),
    )

    assert selected == str(robots[1].id)


def test_excludes_robots_with_unknown_location():
    robots = [
        make_robot("AMR-001", None, 90, RobotStatus.AVAILABLE),
    ]

    assert recommend_robot(robots, "STATION-B3", build_demo_warehouse()) is None


def test_excludes_low_battery_robots():
    robots = [
        make_robot("AMR-001", "STATION-B3", 15, RobotStatus.AVAILABLE),
        make_robot("AMR-002", "STATION-A3", 70, RobotStatus.AVAILABLE),
    ]

    selected = recommend_robot(
        robots,
        "STATION-B3",
        build_demo_warehouse(),
    )

    assert selected == str(robots[1].id)
