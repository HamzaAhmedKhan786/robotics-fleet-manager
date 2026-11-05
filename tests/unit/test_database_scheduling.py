"""Tests for database-backed robot recommendation."""

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from apps.backend.models.mission import Mission, MissionStatus
from apps.backend.models.robot import Robot, RobotStatus
from apps.backend.services.scheduling_service import (
    recommend_robot_for_mission,
)


def make_robot(name, location, battery, status):
    return Robot(
        id=uuid4(),
        name=name,
        current_location=location,
        battery_level=battery,
        status=status,
    )


def make_session(mission, robots):
    session = AsyncMock()
    session.get.return_value = mission

    result = MagicMock()
    result.scalars.return_value.all.return_value = robots
    session.execute.return_value = result

    return session


@pytest.mark.asyncio
async def test_recommends_nearest_available_robot():
    mission_id = uuid4()

    mission = Mission(
        id=mission_id,
        pickup_location="STATION-B3",
        delivery_location="STATION-A1",
        status=MissionStatus.PENDING,
    )

    robots = [
        make_robot("AMR-001", "STATION-A1", 80, RobotStatus.AVAILABLE),
        make_robot("AMR-002", "STATION-B2", 70, RobotStatus.AVAILABLE),
    ]

    session = make_session(mission, robots)

    selected = await recommend_robot_for_mission(session, mission_id)

    assert selected == str(robots[1].id)
    session.get.assert_awaited_once_with(Mission, mission_id)
    session.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_missing_mission_returns_none():
    mission_id = uuid4()
    session = make_session(None, [])

    selected = await recommend_robot_for_mission(session, mission_id)

    assert selected is None
    session.execute.assert_not_awaited()


@pytest.mark.asyncio
async def test_completed_mission_returns_none():
    mission_id = uuid4()

    mission = Mission(
        id=mission_id,
        pickup_location="STATION-A1",
        delivery_location="STATION-B3",
        status=MissionStatus.COMPLETED,
    )

    session = make_session(mission, [])

    selected = await recommend_robot_for_mission(session, mission_id)

    assert selected is None
    session.execute.assert_not_awaited()


@pytest.mark.asyncio
async def test_no_available_robot_returns_none():
    mission_id = uuid4()

    mission = Mission(
        id=mission_id,
        pickup_location="STATION-B3",
        delivery_location="STATION-A1",
        status=MissionStatus.PENDING,
    )

    robots = [
        make_robot("AMR-001", "STATION-A1", 80, RobotStatus.OFFLINE),
        make_robot("AMR-002", "STATION-B2", 15, RobotStatus.AVAILABLE),
    ]

    session = make_session(mission, robots)

    selected = await recommend_robot_for_mission(session, mission_id)

    assert selected is None
