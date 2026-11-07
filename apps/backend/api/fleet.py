"""Dashboard-oriented read-only fleet endpoints."""

from collections import Counter
from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.backend.db.session import get_db
from apps.backend.models.mission import Mission, MissionStatus
from apps.backend.models.robot import Robot, RobotStatus
from apps.backend.services.advanced_motion import STATIONS
from apps.backend.services.warehouse_graph import build_demo_warehouse

router = APIRouter(
    prefix="/api/v1/fleet",
    tags=["Fleet"],
)

DbSession = Annotated[AsyncSession, Depends(get_db)]


class FleetSummary(BaseModel):
    total_robots: int
    active_robots: int
    available_robots: int
    charging_robots: int
    offline_robots: int
    total_missions: int
    active_missions: int
    pending_missions: int
    completed_missions: int
    robots_by_status: dict[str, int]
    missions_by_status: dict[str, int]


class WarehouseEdge(BaseModel):
    source: str
    target: str
    distance: float


class WarehouseMap(BaseModel):
    stations: list[str]
    edges: list[WarehouseEdge]
    positions: dict[str, tuple[float, float, float]]


@router.get("/summary", response_model=FleetSummary)
async def fleet_summary(
    session: DbSession,
) -> FleetSummary:
    robot_statuses = (await session.execute(select(Robot.status))).scalars().all()

    mission_statuses = (await session.execute(select(Mission.status))).scalars().all()

    robot_counts = Counter(status.value for status in robot_statuses)

    mission_counts = Counter(status.value for status in mission_statuses)

    return FleetSummary(
        total_robots=len(robot_statuses),
        active_robots=robot_counts[RobotStatus.BUSY.value],
        available_robots=robot_counts[RobotStatus.AVAILABLE.value],
        charging_robots=robot_counts[RobotStatus.CHARGING.value],
        offline_robots=robot_counts[RobotStatus.OFFLINE.value],
        total_missions=len(mission_statuses),
        active_missions=(
            mission_counts[MissionStatus.ASSIGNED.value]
            + mission_counts[MissionStatus.IN_PROGRESS.value]
        ),
        pending_missions=mission_counts[MissionStatus.PENDING.value],
        completed_missions=mission_counts[MissionStatus.COMPLETED.value],
        robots_by_status={item.value: robot_counts[item.value] for item in RobotStatus},
        missions_by_status={
            item.value: mission_counts[item.value] for item in MissionStatus
        },
    )


@router.get("/warehouse", response_model=WarehouseMap)
async def warehouse_map() -> WarehouseMap:
    graph = build_demo_warehouse()

    edges = [
        WarehouseEdge(
            source=start,
            target=end,
            distance=distance,
        )
        for start, neighbors in graph.items()
        for end, distance in neighbors.items()
        if start < end
    ]

    return WarehouseMap(
        stations=list(graph),
        edges=edges,
        positions={name: (x, 0.0, z) for name, (x, z) in STATIONS.items()},
    )
