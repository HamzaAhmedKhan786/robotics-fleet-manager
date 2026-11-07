from math import isclose

import pytest

from apps.backend.services.advanced_motion import (
    STATIONS,
    MotionLimits,
    sample_path,
    travel_duration,
    warehouse_edges,
)
from apps.backend.services.mission_checkpoint import Checkpoint, transition
from apps.backend.services.traffic_control import MoveIntent, arbitrate


def test_graph_weights_match_display():
    graph = warehouse_edges()
    assert graph["STATION-A1"]["STATION-A2"] == 6.0
    assert graph["STATION-A1"]["STATION-B1"] == 8.0


def test_trapezoidal_speed_and_final_position():
    route = ["STATION-A1", "STATION-A2", "STATION-A3"]
    duration = travel_duration(12, MotionLimits())
    assert isclose(sample_path(route, duration).progress, 1.0)
    assert sample_path(route, duration).speed == 0
    assert sample_path(route, duration).x == STATIONS["STATION-A3"][0]
    assert sample_path(route, 0).speed == 0
    assert 0 < sample_path(route, duration / 2).progress < 1


def test_motion_rejects_invalid_input():
    with pytest.raises(ValueError):
        sample_path(["nonexistent"], 1)


def test_reservation_blocks_same_target():
    intents = [
        MoveIntent("a", (-6, -4), (0, -4), 5),
        MoveIntent("b", (6, -4), (0, -4), 2),
    ]
    accepted, waiting = arbitrate(intents, {"a": (-6, -4), "b": (6, -4)})
    assert len(accepted) == 1 and len(waiting) == 1
    assert accepted[0].robot_id == "a"


def test_checkpoint_pause_resume():
    cp = transition(Checkpoint(), "advance", 10, 2)
    cp = transition(cp, "pause", 10)
    with pytest.raises(ValueError):
        transition(cp, "advance", 10, 3)
    cp = transition(cp, "resume", 10)
    cp = transition(cp, "advance", 10, 8)
    assert cp.completed and cp.elapsed == 10


def test_arbitration_supports_fifteen_independent_robots():
    intents = [
        MoveIntent(f"robot-{index:02d}", (index * 10.0, 0.0), (index * 10.0 + 1.0, 0.0))
        for index in range(15)
    ]
    occupied = {intent.robot_id: intent.origin for intent in intents}
    accepted, waiting = arbitrate(intents, occupied)
    assert len(accepted) == 15
    assert not waiting


def test_crossing_routes_are_not_simultaneously_accepted():
    intents = [
        MoveIntent("vertical", (0.0, -2.0), (0.0, 2.0), priority=5),
        MoveIntent("horizontal", (-2.0, 0.0), (2.0, 0.0), priority=3),
    ]
    accepted, waiting = arbitrate(intents, {item.robot_id: item.origin for item in intents})
    assert len(accepted) == 1
    assert len(waiting) == 1


def test_checkpoint_version_increases_for_recovery():
    cp = Checkpoint(elapsed=4, version=8)
    cp = transition(cp, "pause", duration=10)
    cp = transition(cp, "resume", duration=10)
    cp = transition(cp, "advance", duration=10, delta=2)
    assert cp.elapsed == 6
    assert cp.version == 11


def test_segment_profile_stops_at_station_waypoints():
    from apps.backend.services.advanced_motion import route_duration, sample_segments
    route = ["STATION-A1", "STATION-A2", "STATION-B2"]
    first_duration = travel_duration(6)
    at_waypoint = sample_segments(route, first_duration)
    assert isclose(at_waypoint.x, 0.0)
    assert isclose(at_waypoint.z, -4.0)
    assert at_waypoint.speed == 0.0
    after_corner = sample_segments(route, first_duration + 0.4)
    assert after_corner.z > -4.0
    assert isclose(sample_segments(route, route_duration(route)).progress, 1.0)
