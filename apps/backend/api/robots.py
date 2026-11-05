"""API endpoints for robot management."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from apps.backend.db.session import get_db
from apps.backend.schemas.robot import (
    RobotCreate,
    RobotResponse,
    RobotUpdate,
)
from apps.backend.services.robot_service import (
    create_robot,
    get_robot,
    list_robots,
    update_robot,
)

router = APIRouter(
    prefix="/api/v1/robots",
    tags=["Robots"],
)

DbSession = Annotated[AsyncSession, Depends(get_db)]


@router.post(
    "",
    response_model=RobotResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register_robot(
    data: RobotCreate,
    session: DbSession,
):
    try:
        return await create_robot(session, data)
    except IntegrityError:
        await session.rollback()
        raise HTTPException(
            status_code=409,
            detail="A robot with this name already exists.",
        ) from None


@router.get("", response_model=list[RobotResponse])
async def get_robots(session: DbSession):
    return await list_robots(session)


@router.get("/{robot_id}", response_model=RobotResponse)
async def get_robot_by_id(
    robot_id: UUID,
    session: DbSession,
):
    robot = await get_robot(session, robot_id)

    if robot is None:
        raise HTTPException(
            status_code=404,
            detail="Robot not found.",
        )

    return robot


@router.patch("/{robot_id}", response_model=RobotResponse)
async def edit_robot(
    robot_id: UUID,
    data: RobotUpdate,
    session: DbSession,
):
    return await update_robot(session, robot_id, data)
