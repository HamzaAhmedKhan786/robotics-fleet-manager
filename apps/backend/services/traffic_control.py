"""Discrete conservative traffic arbitration for warehouse simulations.

Conflicts are detected before committing movement; not physical collision protection.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import hypot


@dataclass(frozen=True)
class MoveIntent:
    robot_id: str
    origin: tuple[float, float]
    target: tuple[float, float]
    priority: int = 3


def distance_point_to_segment(point: tuple[float, float], a: tuple[float, float], b: tuple[float, float]) -> float:
    vx, vz = b[0] - a[0], b[1] - a[1]
    norm2 = vx * vx + vz * vz
    if norm2 == 0:
        return hypot(point[0] - a[0], point[1] - a[1])
    t = max(0.0, min(1.0, ((point[0] - a[0]) * vx + (point[1] - a[1]) * vz) / norm2))
    return hypot(point[0] - a[0] - t * vx, point[1] - a[1] - t * vz)


def segment_separation(a: MoveIntent, b: MoveIntent) -> float:
    """Minimum separation of two proposed segments, including intersections."""
    ax, az = a.origin
    bx, bz = a.target
    cx, cz = b.origin
    dx, dz = b.target
    def cross(x: float, y: float, u: float, v: float) -> float:
        return x * v - y * u
    r = (bx - ax, bz - az)
    s = (dx - cx, dz - cz)
    denominator = cross(*r, *s)
    q = (cx - ax, cz - az)
    if abs(denominator) > 1e-12:
        t = cross(*q, *s) / denominator
        u = cross(*q, *r) / denominator
        if 0 <= t <= 1 and 0 <= u <= 1:
            return 0.0
    return min(
        distance_point_to_segment(a.origin, b.origin, b.target),
        distance_point_to_segment(a.target, b.origin, b.target),
        distance_point_to_segment(b.origin, a.origin, a.target),
        distance_point_to_segment(b.target, a.origin, a.target),
    )


def arbitrate(intents: list[MoveIntent], occupied: dict[str, tuple[float, float]], clearance: float = 1.2) -> tuple[list[MoveIntent], list[MoveIntent]]:
    """Prioritize moves, and reject segments near occupied or already reserved segments.

    Occupied includes ALL other robots, including offline and waiting robots.
    A blocked robot stays in place. When a robot is held, its position remains an obstacle.
    """
    if clearance <= 0:
        raise ValueError("clearance must be positive")
    accepted: list[MoveIntent] = []
    waiting: list[MoveIntent] = []
    by_id = {i.robot_id: i for i in intents}
    for intent in sorted(intents, key=lambda i: (-i.priority, i.robot_id)):
        unsafe = any(
            distance_point_to_segment(position, intent.origin, intent.target) < clearance
            for rid, position in occupied.items()
            if rid != intent.robot_id and rid not in {a.robot_id for a in accepted}
            and (rid not in by_id or by_id[rid] in waiting)
        )
        unsafe |= any(segment_separation(intent, earlier) < clearance for earlier in accepted)
        if unsafe:
            waiting.append(intent)
        else:
            accepted.append(intent)
    # Safety pass: accepted trajectories must not approach any robots subsequently held.
    blocked = {i.robot_id for i in waiting}
    if blocked:
        for intent in accepted[:]:
            if any(distance_point_to_segment(occupied[rid], intent.origin, intent.target) < clearance for rid in blocked if rid in occupied):
                accepted.remove(intent)
                waiting.append(intent)
    return accepted, waiting
