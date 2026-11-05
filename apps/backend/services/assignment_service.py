"""Transactional mission assignment and lifecycle operations.

Locking order is always mission first, then robots in UUID order.
This MVP locks available robot rows to prevent double booking.
"""

from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.backend.models.mission import Mission, MissionStatus
from apps.backend.models.robot import Robot, RobotStatus
from apps.backend.services.scheduling_service import recommend_robot
from apps.backend.services.warehouse_graph import build_demo_warehouse


async def _locked_mission(
    session: AsyncSession,
    mission_id: UUID,
) -> Mission:
    result = await session.execute(
        select(Mission).where(Mission.id == mission_id).with_for_update()
    )

    mission = result.scalar_one_or_none()

    if mission is None:
        raise HTTPException(
            status_code=404,
            detail="Mission not found.",
        )

    return mission


async def _locked_robot(
    session: AsyncSession,
    robot_id: UUID,
) -> Robot:
    result = await session.execute(
        select(Robot).where(Robot.id == robot_id).with_for_update()
    )

    robot = result.scalar_one_or_none()

    if robot is None:
        raise HTTPException(
            status_code=409,
            detail="Assigned robot no longer exists.",
        )

    return robot


async def assign_mission(
    session: AsyncSession,
    mission_id: UUID,
) -> Mission:
    """Select and reserve an eligible robot atomically."""

    async with session.begin():
        mission = await _locked_mission(session, mission_id)

        if mission.status != MissionStatus.PENDING:
            raise HTTPException(
                status_code=409,
                detail="Mission is not pending.",
            )

        graph = build_demo_warehouse()

        if (
            mission.pickup_location not in graph
            or mission.delivery_location not in graph
        ):
            raise HTTPException(
                status_code=422,
                detail="Mission contains an unknown station.",
            )

        # Lock available robot rows in a deterministic order.
        result = await session.execute(
            select(Robot)
            .where(Robot.status == RobotStatus.AVAILABLE)
            .order_by(Robot.id)
            .with_for_update()
        )

        robots = list(result.scalars().all())

        # Rust chooses the best candidate based on distance and battery.
        selected = recommend_robot(
            robots,
            mission.pickup_location,
            graph,
        )

        if selected is None:
            raise HTTPException(
                status_code=409,
                detail="No eligible robot available.",
            )

        selected_uuid = UUID(selected)

        robot = next(
            (item for item in robots if item.id == selected_uuid),
            None,
        )

        if robot is None or robot.status != RobotStatus.AVAILABLE:
            raise HTTPException(
                status_code=409,
                detail="Robot is no longer available.",
            )

        mission.assigned_robot_id = robot.id
        mission.status = MissionStatus.ASSIGNED
        robot.status = RobotStatus.BUSY

        await session.flush()

    return mission


async def start_mission(
    session: AsyncSession,
    mission_id: UUID,
) -> Mission:
    """Transition an assigned mission to in progress."""

    async with session.begin():
        mission = await _locked_mission(session, mission_id)

        if (
            mission.status != MissionStatus.ASSIGNED
            or mission.assigned_robot_id is None
        ):
            raise HTTPException(
                status_code=409,
                detail="Mission must be assigned first.",
            )

        robot = await _locked_robot(
            session,
            mission.assigned_robot_id,
        )

        if robot.status != RobotStatus.BUSY:
            raise HTTPException(
                status_code=409,
                detail="Reserved robot is not busy.",
            )

        mission.status = MissionStatus.IN_PROGRESS
        await session.flush()

    return mission


async def complete_mission(
    session: AsyncSession,
    mission_id: UUID,
) -> Mission:
    """Simulate delivery completion and release the robot."""

    async with session.begin():
        mission = await _locked_mission(session, mission_id)

        if (
            mission.status != MissionStatus.IN_PROGRESS
            or mission.assigned_robot_id is None
        ):
            raise HTTPException(
                status_code=409,
                detail="Mission is not in progress.",
            )

        robot = await _locked_robot(
            session,
            mission.assigned_robot_id,
        )

        if robot.status != RobotStatus.BUSY:
            raise HTTPException(
                status_code=409,
                detail="Assigned robot is not busy.",
            )

        mission.status = MissionStatus.COMPLETED

        # Simulated delivery: robot reaches the destination.
        robot.current_location = mission.delivery_location

        robot.status = (
            RobotStatus.AVAILABLE if robot.battery_level >= 30 else RobotStatus.CHARGING
        )

        await session.flush()

    return mission


async def cancel_mission(
    session: AsyncSession,
    mission_id: UUID,
) -> Mission:
    """Cancel pending/assigned missions and release reserved robots."""

    async with session.begin():
        mission = await _locked_mission(session, mission_id)

        if mission.status not in (
            MissionStatus.PENDING,
            MissionStatus.ASSIGNED,
        ):
            raise HTTPException(
                status_code=409,
                detail=("Only pending or assigned missions may be cancelled."),
            )

        if mission.assigned_robot_id is not None:
            robot = await _locked_robot(
                session,
                mission.assigned_robot_id,
            )

            if robot.status != RobotStatus.BUSY:
                raise HTTPException(
                    status_code=409,
                    detail="Assigned robot is not busy.",
                )

            robot.status = (
                RobotStatus.AVAILABLE
                if robot.battery_level >= 30
                else RobotStatus.CHARGING
            )

        mission.status = MissionStatus.CANCELLED
        await session.flush()

    return mission
