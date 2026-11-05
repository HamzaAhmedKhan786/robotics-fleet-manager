"""Database operations for robot registration and retrieval."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.backend.models.robot import Robot
from apps.backend.schemas.robot import RobotCreate


async def create_robot(
    session: AsyncSession,
    data: RobotCreate,
) -> Robot:
    """Register a robot in PostgreSQL."""

    robot = Robot(
        name=data.name,
        battery_level=data.battery_level,
    )

    session.add(robot)

    await session.commit()
    await session.refresh(robot)

    return robot


async def list_robots(session: AsyncSession) -> list[Robot]:
    """Retrieve registered robots."""

    result = await session.execute(select(Robot).order_by(Robot.created_at, Robot.id))

    return list(result.scalars().all())


async def get_robot(
    session: AsyncSession,
    robot_id: UUID,
) -> Robot | None:
    """Retrieve a single robot by UUID."""

    return await session.get(Robot, robot_id)
