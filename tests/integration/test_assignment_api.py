"""End-to-end mission lifecycle, summary, and concurrency tests."""

import asyncio
from uuid import uuid4


async def add_robot(
    client,
    name="TEST-AMR-01",
    location="STATION-B2",
    battery=80,
):
    response = await client.post(
        "/api/v1/robots",
        json={
            "name": name,
            "current_location": location,
            "battery_level": battery,
        },
    )

    assert response.status_code == 201

    robot = response.json()

    updated = await client.patch(
        f"/api/v1/robots/{robot['id']}",
        json={"status": "available"},
    )

    assert updated.status_code == 200
    return updated.json()


async def add_mission(client):
    response = await client.post(
        "/api/v1/missions",
        json={
            "pickup_location": "STATION-B3",
            "delivery_location": "STATION-A1",
            "priority": 4,
        },
    )

    assert response.status_code == 201
    return response.json()


async def test_assignment_and_completion_changes_robot_state(client):
    robot = await add_robot(client)
    mission = await add_mission(client)

    assigned = await client.post(f"/api/v1/missions/{mission['id']}/assign")

    assert assigned.status_code == 200
    assert assigned.json()["status"] == "assigned"
    assert assigned.json()["assigned_robot_id"] == robot["id"]

    busy = await client.get(f"/api/v1/robots/{robot['id']}")
    assert busy.json()["status"] == "busy"

    blocked = await client.patch(
        f"/api/v1/robots/{robot['id']}",
        json={"status": "available"},
    )
    assert blocked.status_code == 409

    started = await client.post(f"/api/v1/missions/{mission['id']}/start")
    assert started.status_code == 200
    assert started.json()["status"] == "in_progress"

    completed = await client.post(f"/api/v1/missions/{mission['id']}/complete")
    assert completed.status_code == 200
    assert completed.json()["status"] == "completed"

    free = await client.get(f"/api/v1/robots/{robot['id']}")
    assert free.json()["status"] == "available"
    assert free.json()["current_location"] == "STATION-A1"

    repeated = await client.post(f"/api/v1/missions/{mission['id']}/complete")
    assert repeated.status_code == 409


async def test_no_eligible_robot_returns_conflict(client):
    mission = await add_mission(client)

    response = await client.post(f"/api/v1/missions/{mission['id']}/assign")

    assert response.status_code == 409

    check = await client.get(f"/api/v1/missions/{mission['id']}")
    assert check.json()["status"] == "pending"


async def test_cancel_assigned_mission_releases_robot(client):
    robot = await add_robot(client)
    mission = await add_mission(client)

    assigned = await client.post(f"/api/v1/missions/{mission['id']}/assign")
    assert assigned.status_code == 200

    cancelled = await client.post(f"/api/v1/missions/{mission['id']}/cancel")

    assert cancelled.status_code == 200
    assert cancelled.json()["status"] == "cancelled"

    check = await client.get(f"/api/v1/robots/{robot['id']}")
    assert check.json()["status"] == "available"


async def test_cannot_cancel_in_progress_mission(client):
    await add_robot(client)
    mission = await add_mission(client)

    await client.post(f"/api/v1/missions/{mission['id']}/assign")
    await client.post(f"/api/v1/missions/{mission['id']}/start")

    response = await client.post(f"/api/v1/missions/{mission['id']}/cancel")

    assert response.status_code == 409


async def test_summary_and_warehouse_for_dashboard(client):
    await add_robot(client)
    await add_mission(client)

    summary = await client.get("/api/v1/fleet/summary")

    assert summary.status_code == 200
    assert summary.json()["total_robots"] == 1
    assert summary.json()["available_robots"] == 1
    assert summary.json()["pending_missions"] == 1

    warehouse = await client.get("/api/v1/fleet/warehouse")

    assert warehouse.status_code == 200
    assert "STATION-A1" in warehouse.json()["stations"]
    assert len(warehouse.json()["edges"]) == 7


async def test_two_missions_cannot_reserve_same_robot(client):
    robot = await add_robot(client)
    first = await add_mission(client)
    second = await add_mission(client)

    responses = await asyncio.gather(
        client.post(f"/api/v1/missions/{first['id']}/assign"),
        client.post(f"/api/v1/missions/{second['id']}/assign"),
    )

    assert sorted(item.status_code for item in responses) == [200, 409]

    successful = [item for item in responses if item.status_code == 200]

    assert len(successful) == 1
    assert successful[0].json()["assigned_robot_id"] == robot["id"]


async def test_same_mission_cannot_be_assigned_twice(client):
    await add_robot(client)
    await add_robot(
        client,
        name="TEST-AMR-02",
        location="STATION-A2",
    )

    mission = await add_mission(client)

    responses = await asyncio.gather(
        client.post(f"/api/v1/missions/{mission['id']}/assign"),
        client.post(f"/api/v1/missions/{mission['id']}/assign"),
    )

    assert sorted(item.status_code for item in responses) == [200, 409]


async def test_missing_mission_assignment_returns_404(client):
    response = await client.post(f"/api/v1/missions/{uuid4()}/assign")

    assert response.status_code == 404


async def test_invalid_location_and_battery_cannot_be_available(client):
    response = await client.post(
        "/api/v1/robots",
        json={
            "name": "TEST-LOW",
            "battery_level": 10,
        },
    )

    assert response.status_code == 201
    robot_id = response.json()["id"]

    bad = await client.patch(
        f"/api/v1/robots/{robot_id}",
        json={"status": "available"},
    )

    assert bad.status_code == 409

    bad_location = await client.patch(
        f"/api/v1/robots/{robot_id}",
        json={"current_location": "INVALID"},
    )

    assert bad_location.status_code == 422
