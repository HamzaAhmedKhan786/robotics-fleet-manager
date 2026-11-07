"""Persist positions sampled by Rust for all running simulation missions.

Uses the same mission/robot row-lock order as assignment_service.
Do not run as a separate process: the autonomous worker imports it.
"""
from datetime import UTC, datetime

from sqlalchemy import select

from apps.backend.db.session import AsyncSessionLocal
from apps.backend.models.mission import Mission, MissionStatus
from apps.backend.models.robot import Robot
from apps.backend.services.movement_engine import sample_position


async def advance_running() -> None:
    async with AsyncSessionLocal() as session:
        ids = list((await session.execute(
            select(Mission.id).where(Mission.status == MissionStatus.IN_PROGRESS)
        )).scalars().all())

    for mission_id in ids:
        async with AsyncSessionLocal() as session, session.begin():
                mission = (await session.execute(
                    select(Mission).where(Mission.id == mission_id).with_for_update()
                )).scalar_one_or_none()
                if (mission is None or mission.status != MissionStatus.IN_PROGRESS
                        or mission.assigned_robot_id is None or mission.started_at is None):
                    continue
                robot = (await session.execute(
                    select(Robot).where(Robot.id == mission.assigned_robot_id).with_for_update()
                )).scalar_one_or_none()
                if robot is None:
                    continue
                plan = mission.plan or {}
                stations = plan.get("path", [])
                duration = max(1.0, float(plan.get("duration_seconds", 25)))
                elapsed = max(0.0, (datetime.now(UTC) - mission.started_at).total_seconds())
                if not stations:
                    continue
                x, z, progress = sample_position(stations, elapsed, duration)
                robot.position_x = x
                robot.position_z = z
                robot.movement_progress = progress
                robot.position_updated_at = datetime.now(UTC)
