"""Database operations for missions."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.backend.models.mission import Mission
from apps.backend.schemas.mission import MissionCreate


async def create_mission(
    session: AsyncSession,
    data: MissionCreate,
) -> Mission:
    mission = Mission(
        pickup_location=data.pickup_location,
        delivery_location=data.delivery_location,
        priority=data.priority,
    )

    session.add(mission)
    await session.commit()
    await session.refresh(mission)

    return mission


async def list_missions(
    session: AsyncSession,
) -> list[Mission]:
    result = await session.execute(
        select(Mission).order_by(Mission.created_at, Mission.id)
    )
    return list(result.scalars().all())


async def get_mission(
    session: AsyncSession,
    mission_id: UUID,
) -> Mission | None:
    return await session.get(Mission, mission_id)
