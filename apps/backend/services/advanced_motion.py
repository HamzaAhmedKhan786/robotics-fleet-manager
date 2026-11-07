"""Deterministic, unit-consistent warehouse simulation primitives.

Not a safety-rated motion controller. Distance units are simulated metres.
"""
from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from itertools import pairwise
from math import hypot, isfinite, sqrt

STATIONS: dict[str, tuple[float, float]] = {
    "STATION-A1": (-6.0, -4.0),
    "STATION-A2": (0.0, -4.0),
    "STATION-A3": (6.0, -4.0),
    "STATION-B1": (-6.0, 4.0),
    "STATION-B2": (0.0, 4.0),
    "STATION-B3": (6.0, 4.0),
}


def segment_length(a: tuple[float, float], b: tuple[float, float]) -> float:
    return hypot(b[0] - a[0], b[1] - a[1])


def path_length(points: Iterable[tuple[float, float]]) -> float:
    points = list(points)
    return sum(segment_length(a, b) for a, b in pairwise(points))


def warehouse_edges() -> dict[str, dict[str, float]]:
    """Generate graph edge weights from precisely the coordinates shown in 3D."""
    graph: dict[str, dict[str, float]] = {station: {} for station in STATIONS}
    for prefix in ("A", "B"):
        for n in (1, 2):
            a, b = f"STATION-{prefix}{n}", f"STATION-{prefix}{n+1}"
            cost = segment_length(STATIONS[a], STATIONS[b])
            graph[a][b] = graph[b][a] = cost
    for n in (1, 2, 3):
        a, b = f"STATION-A{n}", f"STATION-B{n}"
        cost = segment_length(STATIONS[a], STATIONS[b])
        graph[a][b] = graph[b][a] = cost
    return graph


@dataclass(frozen=True)
class MotionLimits:
    vmax: float = 2.0  # simulated metres / second
    accel: float = 1.0  # simulated metres / second squared
    decel: float = 1.0

    def __post_init__(self) -> None:
        if not all(isfinite(v) and v > 0 for v in (self.vmax, self.accel, self.decel)):
            raise ValueError("Motion limits must be positive and finite")


DEFAULT_MOTION_LIMITS = MotionLimits()


@dataclass(frozen=True)
class MotionSample:
    x: float
    z: float
    progress: float
    speed: float
    distance: float
    elapsed: float
    duration: float


def travel_duration(length: float, limits: MotionLimits = DEFAULT_MOTION_LIMITS) -> float:
    if not isfinite(length) or length < 0:
        raise ValueError("Invalid travel distance")
    if length == 0:
        return 0.0
    v_peak = sqrt(2 * length / (1 / limits.accel + 1 / limits.decel))
    v = min(limits.vmax, v_peak)
    accel_dist = v * v / (2 * limits.accel)
    decel_dist = v * v / (2 * limits.decel)
    cruise_dist = max(0.0, length - accel_dist - decel_dist)
    return v / limits.accel + cruise_dist / v + v / limits.decel


def distance_at_time(length: float, elapsed: float, limits: MotionLimits = DEFAULT_MOTION_LIMITS) -> tuple[float, float]:
    if not isfinite(length) or length < 0:
        raise ValueError("Invalid travel distance")
    if not isfinite(elapsed):
        raise ValueError("Invalid elapsed time")
    if length == 0:
        return 0.0, 0.0
    peak = sqrt(2 * length / (1 / limits.accel + 1 / limits.decel))
    v = min(limits.vmax, peak)
    ta = v / limits.accel
    da = v * v / (2 * limits.accel)
    dd = v * v / (2 * limits.decel)
    tc = max(0.0, length - da - dd) / v
    t = max(0.0, elapsed)
    if t < ta:
        return 0.5 * limits.accel * t * t, limits.accel * t
    if t < ta + tc:
        return da + v * (t - ta), v
    td = t - ta - tc
    if td < v / limits.decel:
        return da + v * tc + v * td - 0.5 * limits.decel * td * td, max(0.0, v - limits.decel * td)
    return length, 0.0


def sample_path(stations: list[str], elapsed: float, limits: MotionLimits = DEFAULT_MOTION_LIMITS) -> MotionSample:
    if not stations or any(s not in STATIONS for s in stations):
        raise ValueError("Unknown or empty route")
    points = [STATIONS[s] for s in stations]
    total = path_length(points)
    duration = travel_duration(total, limits)
    traveled, speed = distance_at_time(total, elapsed, limits)
    remain = traveled
    x, z = points[0]
    for a, b in pairwise(points):
        length = segment_length(a, b)
        if length <= 0:
            continue
        if remain <= length:
            fraction = remain / length
            x, z = a[0] + (b[0] - a[0]) * fraction, a[1] + (b[1] - a[1]) * fraction
            break
        remain -= length
    else:
        x, z = points[-1]
    return MotionSample(x, z, (traveled / total if total else 1.0), speed, traveled, max(0.0, elapsed), duration)


def route_duration(stations: list[str], limits: MotionLimits = DEFAULT_MOTION_LIMITS) -> float:
    """Total time when the robot stops at each route waypoint before turning."""
    if not stations or any(station not in STATIONS for station in stations):
        raise ValueError("Invalid route")
    return sum(
        travel_duration(segment_length(STATIONS[a], STATIONS[b]), limits)
        for a, b in pairwise(stations)
    )


def sample_segments(stations: list[str], elapsed: float, limits: MotionLimits = DEFAULT_MOTION_LIMITS) -> MotionSample:
    """Acceleration-limited step along each segment, stopping at junctions."""
    if not stations or any(station not in STATIONS for station in stations):
        raise ValueError("Invalid route")
    if not isfinite(elapsed):
        raise ValueError("Invalid elapsed time")
    durations = [
        travel_duration(segment_length(STATIONS[a], STATIONS[b]), limits)
        for a, b in pairwise(stations)
    ]
    total_distance = path_length(STATIONS[s] for s in stations)
    total_duration = sum(durations)
    completed = 0.0
    t = max(0.0, elapsed)
    for (a, b), duration in zip(pairwise(stations), durations):
        length = segment_length(STATIONS[a], STATIONS[b])
        if t <= duration and duration > 0 and length > 0:
            travelled, speed = distance_at_time(length, t, limits)
            fraction = travelled / length
            x = STATIONS[a][0] + (STATIONS[b][0] - STATIONS[a][0]) * fraction
            z = STATIONS[a][1] + (STATIONS[b][1] - STATIONS[a][1]) * fraction
            return MotionSample(x, z, (completed + travelled) / total_distance, speed,
                                completed + travelled, max(0.0, elapsed), total_duration)
        completed += length
        t -= duration
    x, z = STATIONS[stations[-1]]
    return MotionSample(x, z, 1.0, 0.0, total_distance, max(0.0, elapsed), total_duration)
