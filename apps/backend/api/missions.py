"""API endpoints for mission management."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from apps.backend.db.session import get_db
from apps.backend.schemas.mission import MissionCreate, MissionResponse
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


@router.post(
    "",
    response_model=MissionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register_mission(
    data: MissionCreate,
    session: DbSession,
):
    return await create_mission(session, data)


@router.get("", response_model=list[MissionResponse])
async def get_missions(session: DbSession):
    return await list_missions(session)


@router.get("/{mission_id}", response_model=MissionResponse)
async def get_mission_by_id(
    mission_id: UUID,
    session: DbSession,
):
    mission = await get_mission(session, mission_id)

    if mission is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mission not found.",
        )

    return mission
