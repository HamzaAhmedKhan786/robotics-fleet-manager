"""Connect warehouse routing to the Rust scheduling engine."""

from collections.abc import Sequence
from uuid import UUID

import fleet_scheduler
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.backend.models.mission import Mission, MissionStatus
from apps.backend.models.robot import Robot, RobotStatus
from apps.backend.services.warehouse_graph import (
    WarehouseGraph,
    build_demo_warehouse,
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


async def recommend_robot_for_mission(
    session: AsyncSession,
    mission_id: UUID,
) -> str | None:
    """Recommend a robot using mission and robot records from PostgreSQL.

    This function does not assign the mission or update robot status.
    """

    mission = await session.get(Mission, mission_id)

    if mission is None:
        return None

    if mission.status != MissionStatus.PENDING:
        return None

    statement = select(Robot).where(Robot.status == RobotStatus.AVAILABLE)

    result = await session.execute(statement)
    robots = result.scalars().all()

    graph = build_demo_warehouse()

    return recommend_robot(
        robots=robots,
        pickup_location=mission.pickup_location,
        graph=graph,
    )
