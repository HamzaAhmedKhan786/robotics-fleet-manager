"""Database operations for robot registration, retrieval and telemetry."""

from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.backend.models.robot import Robot, RobotStatus
from apps.backend.schemas.robot import RobotCreate, RobotResponse, RobotUpdate
from apps.backend.services.warehouse_graph import build_demo_warehouse


async def create_robot(
    session: AsyncSession,
    data: RobotCreate,
) -> Robot:
    robot = Robot(
        name=data.name,
        battery_level=data.battery_level,
        current_location=data.current_location,
    )

    session.add(robot)
    await session.commit()
    await session.refresh(robot)

    return robot


async def list_robots(
    session: AsyncSession,
) -> list[Robot]:
    result = await session.execute(select(Robot).order_by(Robot.created_at, Robot.id))
    return list(result.scalars().all())


async def get_robot(
    session: AsyncSession,
    robot_id: UUID,
) -> Robot | None:
    return await session.get(Robot, robot_id)


async def update_robot(
    session: AsyncSession,
    robot_id: UUID,
    data: RobotUpdate,
) -> RobotResponse:
    """Update an idle robot and return a fully loaded API response."""

    async with session.begin():
        result = await session.execute(
            select(Robot).where(Robot.id == robot_id).with_for_update()
        )

        robot = result.scalar_one_or_none()

        if robot is None:
            raise HTTPException(
                status_code=404,
                detail="Robot not found.",
            )

        if robot.status == RobotStatus.BUSY:
            raise HTTPException(
                status_code=409,
                detail="Busy robot cannot be edited during an active mission.",
            )

        changes = data.model_dump(exclude_unset=True)

        if any(value is None for value in changes.values()):
            raise HTTPException(
                status_code=422,
                detail="Use explicit values, not null.",
            )

        if changes.get("status") == RobotStatus.BUSY:
            raise HTTPException(
                status_code=409,
                detail="Busy status is managed by missions.",
            )

        location = changes.get(
            "current_location",
            robot.current_location,
        )
        battery = changes.get(
            "battery_level",
            robot.battery_level,
        )
        new_status = changes.get("status", robot.status)

        if location is not None and location not in build_demo_warehouse():
            raise HTTPException(
                status_code=422,
                detail="Unknown warehouse station.",
            )

        if new_status == RobotStatus.AVAILABLE and (location is None or battery < 30):
            raise HTTPException(
                status_code=409,
                detail=(
                    "Available robots need a known location and at least 30% battery."
                ),
            )

        for field, value in changes.items():
            setattr(robot, field, value)

        await session.flush()

    # The transaction has committed.
    # Explicitly load updated_at and other database-generated values.
    await session.refresh(robot)

    # Convert to Pydantic while all attributes are loaded.
    # FastAPI will not need to access expired SQLAlchemy attributes.
    return RobotResponse.model_validate(robot)
