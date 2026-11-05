
"""Connect warehouse routing to the Rust scheduling engine."""

from collections.abc import Sequence

import fleet_scheduler

from apps.backend.models.robot import Robot, RobotStatus
from apps.backend.services.warehouse_graph import (
    WarehouseGraph,
    shortest_distance,
)


def recommend_robot(
    robots: Sequence[Robot],
    pickup_location: str,
    graph: WarehouseGraph,
) -> str | None:
    """Recommend the best eligible robot without modifying the database."""

    candidates: list[tuple[str, bool, float, float]] = []

    for robot in robots:
        if robot.status != RobotStatus.AVAILABLE:
            continue

        if robot.current_location is None:
            continue

        distance = shortest_distance(
            graph,
            robot.current_location,
            pickup_location,
        )

        if distance is None:
            continue

        candidates.append(
            (
                str(robot.id),
                True,
                float(robot.battery_level),
                distance,
            )
        )

    return fleet_scheduler.select_robot(candidates)
