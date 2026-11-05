"""API endpoints for mission management."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from apps.backend.db.session import get_db
from apps.backend.models.mission import Mission
from apps.backend.schemas.mission import MissionCreate, MissionResponse
from apps.backend.services.assignment_service import (
    assign_mission,
    cancel_mission,
    complete_mission,
    start_mission,
)
from apps.backend.services.mission_service import (
    create_mission,
    get_mission,
    list_missions,
)

router = APIRouter(
    prefix="/api/v1/missions",
    tags=["Missions"],
)

DbSession = Annotated[AsyncSession, Depends(get_db)]


async def serialize_mission(
    session: AsyncSession,
    mission: Mission | MissionResponse,
) -> MissionResponse:
    """Return a fully loaded, database-backed mission response."""

    # The service may already return a Pydantic response.
    if isinstance(mission, MissionResponse):
        return mission

    # Explicit asynchronous refresh prevents MissingGreenlet
    # when FastAPI attempts to read database-generated timestamps.
    await session.refresh(mission)

    return MissionResponse.model_validate(mission)


@router.post(
    "",
    response_model=MissionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register_mission(
    data: MissionCreate,
    session: DbSession,
) -> MissionResponse:
    mission = await create_mission(session, data)
    return await serialize_mission(session, mission)


@router.get("", response_model=list[MissionResponse])
async def get_missions(
    session: DbSession,
) -> list[MissionResponse]:
    missions = await list_missions(session)

    return [MissionResponse.model_validate(mission) for mission in missions]


@router.get(
    "/{mission_id}",
    response_model=MissionResponse,
)
async def get_mission_by_id(
    mission_id: UUID,
    session: DbSession,
) -> MissionResponse:
    mission = await get_mission(session, mission_id)

    if mission is None:
        raise HTTPException(
            status_code=404,
            detail="Mission not found.",
        )

    return await serialize_mission(session, mission)


@router.post(
    "/{mission_id}/assign",
    response_model=MissionResponse,
)
async def assign(
    mission_id: UUID,
    session: DbSession,
) -> MissionResponse:
    mission = await assign_mission(session, mission_id)
    return await serialize_mission(session, mission)


@router.post(
    "/{mission_id}/start",
    response_model=MissionResponse,
)
async def start(
    mission_id: UUID,
    session: DbSession,
) -> MissionResponse:
    mission = await start_mission(session, mission_id)
    return await serialize_mission(session, mission)


@router.post(
    "/{mission_id}/complete",
    response_model=MissionResponse,
)
async def complete(
    mission_id: UUID,
    session: DbSession,
) -> MissionResponse:
    mission = await complete_mission(session, mission_id)
    return await serialize_mission(session, mission)


@router.post(
    "/{mission_id}/cancel",
    response_model=MissionResponse,
)
async def cancel(
    mission_id: UUID,
    session: DbSession,
) -> MissionResponse:
    mission = await cancel_mission(session, mission_id)
    return await serialize_mission(session, mission)
