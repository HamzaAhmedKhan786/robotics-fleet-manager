"""Transactional robot assignment and mission lifecycle."""

from datetime import UTC, datetime
from uuid import UUID

import fleet_scheduler
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.backend.models.mission import Mission, MissionStatus
from apps.backend.models.robot import Robot, RobotStatus
from apps.backend.schemas.mission import MissionResponse
from apps.backend.services.route_planner import calculate_plan
from apps.backend.services.warehouse_graph import build_demo_warehouse


async def locked_mission(
    session: AsyncSession,
    mission_id: UUID,
) -> Mission:
    result = await session.execute(
        select(Mission).where(Mission.id == mission_id).with_for_update()
    )
    mission = result.scalar_one_or_none()

    if mission is None:
        raise HTTPException(404, "Mission not found.")

    return mission


async def locked_robot(
    session: AsyncSession,
    robot_id: UUID,
) -> Robot:
    result = await session.execute(
        select(Robot).where(Robot.id == robot_id).with_for_update()
    )
    robot = result.scalar_one_or_none()

    if robot is None:
        raise HTTPException(409, "Assigned robot not found.")

    return robot


async def serialize(
    session: AsyncSession,
    mission: Mission,
) -> MissionResponse:
    # Refresh after commit to load database-generated timestamps.
    await session.refresh(mission)
    return MissionResponse.model_validate(mission)


async def assign_mission(
    session: AsyncSession,
    mission_id: UUID,
) -> MissionResponse:
    """Find a route-feasible robot and reserve it atomically."""

    async with session.begin():
        mission = await locked_mission(session, mission_id)

        if mission.status != MissionStatus.PENDING:
            raise HTTPException(409, "Mission is not pending.")

        graph = build_demo_warehouse()

        if (
            mission.pickup_location not in graph
            or mission.delivery_location not in graph
        ):
            raise HTTPException(422, "Unknown warehouse station.")

        result = await session.execute(
            select(Robot)
            .where(Robot.status == RobotStatus.AVAILABLE)
            .order_by(Robot.id)
            .with_for_update()
        )
        robots = list(result.scalars().all())

        eligible: dict[str, tuple[Robot, dict]] = {}
        candidates: list[tuple[str, bool, float, float]] = []

        for robot in robots:
            if not robot.current_location:
                continue

            plan = calculate_plan(
                graph=graph,
                robot_station=robot.current_location,
                pickup=mission.pickup_location,
                delivery=mission.delivery_location,
                battery=robot.battery_level,
            )

            if plan is None or not plan["feasible"]:
                continue

            robot_id = str(robot.id)
            eligible[robot_id] = (robot, plan)

            candidates.append(
                (
                    robot_id,
                    True,
                    float(robot.battery_level),
                    float(plan["pickup_distance"]),
                )
            )

        # Existing compiled PyO3 / Rust implementation.
        selected_id = fleet_scheduler.select_robot(candidates)

        if selected_id is None:
            raise HTTPException(
                409,
                "No robot can complete this mission with the required battery reserve.",
            )

        selected_robot, selected_plan = eligible[selected_id]

        same_distance = [
            item
            for item in eligible.values()
            if abs(item[1]["pickup_distance"] - selected_plan["pickup_distance"]) < 1e-9
        ]

        reason = (
            f"{selected_robot.name} selected from "
            f"{len(eligible)} feasible robots. "
            f"Distance to pickup: "
            f"{selected_plan['pickup_distance']:.1f} units. "
            f"Complete route: "
            f"{selected_plan['total_distance']:.1f} units. "
            f"Estimated energy: "
            f"{selected_plan['energy_required']:.2f}%. "
            f"Battery: {selected_robot.battery_level:.1f}% -> "
            f"{selected_plan['battery_after']:.1f}%. "
            f"Safety reserve: "
            f"{selected_plan['safety_reserve']:.0f}%."
        )

        if len(same_distance) > 1:
            reason += (
                " Multiple feasible robots had the same pickup "
                "distance; higher battery was preferred, "
                "followed by deterministic robot ID."
            )
        else:
            reason += (
                " This robot had the shortest pickup distance "
                "among feasible candidates."
            )

        mission.assigned_robot_id = selected_robot.id
        mission.status = MissionStatus.ASSIGNED
        mission.plan = selected_plan
        mission.selection_reason = reason
        selected_robot.status = RobotStatus.BUSY

        await session.flush()

    return await serialize(session, mission)


async def start_mission(
    session: AsyncSession,
    mission_id: UUID,
) -> MissionResponse:
    """Start a mission reserved for a robot."""

    async with session.begin():
        mission = await locked_mission(session, mission_id)

        if (
            mission.status != MissionStatus.ASSIGNED
            or mission.assigned_robot_id is None
        ):
            raise HTTPException(409, "Mission must be assigned first.")

        robot = await locked_robot(
            session,
            mission.assigned_robot_id,
        )

        if robot.status != RobotStatus.BUSY:
            raise HTTPException(409, "Reserved robot is not busy.")

        mission.status = MissionStatus.IN_PROGRESS
        mission.started_at = datetime.now(UTC)

        await session.flush()

    return await serialize(session, mission)


async def complete_mission(
    session: AsyncSession,
    mission_id: UUID,
) -> MissionResponse:
    """Finish a simulated mission and release its robot."""

    async with session.begin():
        mission = await locked_mission(session, mission_id)

        if (
            mission.status != MissionStatus.IN_PROGRESS
            or mission.assigned_robot_id is None
        ):
            raise HTTPException(409, "Mission is not in progress.")

        robot = await locked_robot(
            session,
            mission.assigned_robot_id,
        )

        if robot.status != RobotStatus.BUSY:
            raise HTTPException(409, "Assigned robot is not busy.")

        plan = mission.plan or {}
        consumption = float(plan.get("energy_required", 0.0))

        robot.battery_level = max(
            0.0,
            round(robot.battery_level - consumption, 2),
        )
        robot.current_location = mission.delivery_location

        robot.status = (
            RobotStatus.AVAILABLE if robot.battery_level >= 30 else RobotStatus.CHARGING
        )

        mission.status = MissionStatus.COMPLETED
        mission.finished_at = datetime.now(UTC)

        await session.flush()

    return await serialize(session, mission)


async def cancel_mission(
    session: AsyncSession,
    mission_id: UUID,
) -> MissionResponse:
    """Cancel a mission before simulated movement begins."""

    async with session.begin():
        mission = await locked_mission(session, mission_id)

        if mission.status not in (
            MissionStatus.PENDING,
            MissionStatus.ASSIGNED,
        ):
            raise HTTPException(
                409,
                "Only pending or assigned missions can be cancelled.",
            )

        if mission.assigned_robot_id is not None:
            robot = await locked_robot(
                session,
                mission.assigned_robot_id,
            )

            if robot.status != RobotStatus.BUSY:
                raise HTTPException(409, "Assigned robot is not busy.")

            robot.status = (
                RobotStatus.AVAILABLE
                if robot.battery_level >= 30
                else RobotStatus.CHARGING
            )

        mission.status = MissionStatus.CANCELLED
        mission.finished_at = datetime.now(UTC)

        await session.flush()

    return await serialize(session, mission)
