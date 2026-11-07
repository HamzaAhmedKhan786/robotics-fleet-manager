
"""Autonomous fleet dispatcher and simulated mission executor.

Run manually:
    pixi run python -m scripts.auto_worker

Or let FastAPI start it through its lifespan handler.

Only one worker process should run for this local demonstration.
"""

import asyncio
import logging
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select

from apps.backend.core.config import settings
from apps.backend.db.session import AsyncSessionLocal
from apps.backend.models.mission import Mission, MissionStatus
from apps.backend.services.advanced_tick import advance_running
from apps.backend.services.assignment_service import (
    assign_mission,
    complete_mission,
    start_mission,
)
from apps.backend.services.worker_lease import run_exclusive_tick

logger = logging.getLogger("fleet-worker")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)


async def mission_ids(status: MissionStatus) -> list[UUID]:
    """Return mission IDs, with higher priority processed first."""

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Mission.id)
            .where(Mission.status == status)
            .order_by(
                Mission.priority.desc(),
                Mission.created_at,
                Mission.id,
            )
        )
        return list(result.scalars().all())


async def dispatch_pending() -> None:
    """Assign pending missions to eligible robots."""

    for mission_id in await mission_ids(MissionStatus.PENDING):
        async with AsyncSessionLocal() as session:
            try:
                mission = await assign_mission(session, mission_id)

                logger.info(
                    "ASSIGNED mission=%s robot=%s path=%s",
                    mission.id,
                    mission.assigned_robot_id,
                    (mission.plan or {}).get("path", []),
                )

            except HTTPException as exc:
                # No eligible robot or invalid mission:
                # leave it pending until conditions change.
                if exc.status_code not in (404, 409, 422):
                    raise

                logger.debug(
                    "Mission %s not dispatched: %s",
                    mission_id,
                    exc.detail,
                )


async def start_assigned() -> None:
    """Automatically start missions with reserved robots."""

    for mission_id in await mission_ids(MissionStatus.ASSIGNED):
        async with AsyncSessionLocal() as session:
            try:
                mission = await start_mission(session, mission_id)

                logger.info(
                    "STARTED mission=%s duration=%ss",
                    mission.id,
                    (mission.plan or {}).get(
                        "duration_seconds",
                        25,
                    ),
                )

            except HTTPException as exc:
                if exc.status_code not in (404, 409):
                    raise


async def finish_due() -> None:
    """Complete only after persisted simulator progress reaches destination."""
    from apps.backend.models.robot import Robot

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Mission.id)
            .join(Robot, Mission.assigned_robot_id == Robot.id)
            .where(Mission.status == MissionStatus.IN_PROGRESS)
            .where(Robot.movement_progress >= 1.0)
        )
        complete_ids = list(result.scalars().all())

    for mission_id in complete_ids:
        async with AsyncSessionLocal() as session:
            try:
                mission = await complete_mission(session, mission_id)
                logger.info("COMPLETED mission=%s robot=%s", mission.id, mission.assigned_robot_id)
            except HTTPException as exc:
                if exc.status_code not in (404, 409):
                    raise


async def tick() -> None:
    """Execute one autonomous scheduling cycle."""

    await dispatch_pending()
    await start_assigned()
    await advance_running()
    await finish_due()


async def main() -> None:
    """Continuously process missions until the worker is stopped."""

    if not settings.simulation_enabled:
        raise RuntimeError(
            "Autonomous simulation is disabled. "
            "Set SIMULATION_ENABLED=true in .env."
        )

    if settings.postgres_db == "robotics_fleet_test":
        raise RuntimeError(
            "Refusing to run the worker against the test database."
        )

    logger.info(
        "Autonomous worker running on database %s",
        settings.postgres_db,
    )

    while True:
        try:
            await run_exclusive_tick(tick)

        except asyncio.CancelledError:
            logger.info("Autonomous worker stopping.")
            raise

        except Exception:
            logger.exception("Simulation worker tick failed.")

        await asyncio.sleep(
            settings.simulation_tick_seconds
        )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Autonomous worker stopped.")
