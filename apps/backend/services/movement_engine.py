"""Shared 2D digital-twin layout and compiled Rust movement adapter.

Coordinates are warehouse display-space X/Z units; these are simulated
positions, not physical-world localization or safety-certified telemetry.
"""
from collections.abc import Sequence

import fleet_scheduler

STATION_COORDINATES: dict[str, tuple[float, float]] = {
    "STATION-A1": (-6.0, -4.0),
    "STATION-A2": (0.0, -4.0),
    "STATION-A3": (6.0, -4.0),
    "STATION-B1": (-6.0, 4.0),
    "STATION-B2": (0.0, 4.0),
    "STATION-B3": (6.0, 4.0),
}


def station_position(station: str | None) -> tuple[float, float] | None:
    return STATION_COORDINATES.get(station or "")


def sample_position(
    route: Sequence[str], elapsed_seconds: float, duration_seconds: float
) -> tuple[float, float, float]:
    """Call Rust to compute (x, z, fraction) for a mission route."""
    coordinates: list[tuple[float, float]] = []
    for station in route:
        position = station_position(station)
        if position is None:
            raise ValueError(f"Unsupported station in route: {station}")
        coordinates.append(position)
    return fleet_scheduler.sample_route(
        coordinates, float(elapsed_seconds), float(duration_seconds)
    )
