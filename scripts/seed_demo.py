"""Seed a small demo fleet without deleting existing records.

Run: pixi run python -m scripts.seed_demo
Only use with your local development database.
"""

import asyncio

from sqlalchemy import select

from apps.backend.db.session import AsyncSessionLocal
from apps.backend.models.mission import Mission, MissionStatus
from apps.backend.models.robot import Robot, RobotStatus


async def main() -> None:
    robots = [
        ("DEMO-AMR-01", "STATION-A1", 85.0),
        ("DEMO-AMR-02", "STATION-B2", 72.0),
        ("DEMO-AMR-03", "STATION-A3", 64.0),
        ("DEMO-AMR-04", "STATION-B1", 45.0),
    ]

    async with AsyncSessionLocal() as session, session.begin():
        for name, location, battery in robots:
            existing = await session.scalar(select(Robot).where(Robot.name == name))

            if existing is None:
                session.add(
                    Robot(
                        name=name,
                        current_location=location,
                        battery_level=battery,
                        status=RobotStatus.AVAILABLE,
                    )
                )

        existing_mission = await session.scalar(
            select(Mission).where(
                Mission.pickup_location == "STATION-B3",
                Mission.delivery_location == "STATION-A1",
                Mission.status == MissionStatus.PENDING,
            )
        )

        if existing_mission is None:
            session.add(
                Mission(
                    pickup_location="STATION-B3",
                    delivery_location="STATION-A1",
                    priority=4,
                )
            )

    print(
        "Demo robots and a pending mission are ready. Existing records were preserved."
    )


if __name__ == "__main__":
    asyncio.run(main())
