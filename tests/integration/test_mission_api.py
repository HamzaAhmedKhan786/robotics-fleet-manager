"""Integration tests for Mission API endpoints."""

from uuid import uuid4


async def test_create_mission(client):
    response = await client.post(
        "/api/v1/missions",
        json={
            "pickup_location": "STATION-A1",
            "delivery_location": "STATION-B3",
            "priority": 3,
        },
    )

    assert response.status_code == 201

    mission = response.json()
    assert mission["pickup_location"] == "STATION-A1"
    assert mission["delivery_location"] == "STATION-B3"
    assert mission["priority"] == 3
    assert mission["status"] == "pending"
    assert mission["assigned_robot_id"] is None
    assert "id" in mission


async def test_list_missions(client):
    await client.post(
        "/api/v1/missions",
        json={
            "pickup_location": "A1",
            "delivery_location": "B1",
        },
    )

    response = await client.get("/api/v1/missions")

    assert response.status_code == 200
    assert len(response.json()) == 1


async def test_get_mission_by_id(client):
    created = await client.post(
        "/api/v1/missions",
        json={
            "pickup_location": "A1",
            "delivery_location": "B1",
        },
    )

    assert created.status_code == 201
    mission_id = created.json()["id"]

    response = await client.get(f"/api/v1/missions/{mission_id}")

    assert response.status_code == 200
    assert response.json()["id"] == mission_id


async def test_invalid_priority(client):
    response = await client.post(
        "/api/v1/missions",
        json={
            "pickup_location": "A1",
            "delivery_location": "B1",
            "priority": 10,
        },
    )

    assert response.status_code == 422


async def test_missing_pickup_location(client):
    response = await client.post(
        "/api/v1/missions",
        json={
            "delivery_location": "B1",
            "priority": 3,
        },
    )

    assert response.status_code == 422


async def test_mission_not_found(client):
    mission_id = uuid4()

    response = await client.get(f"/api/v1/missions/{mission_id}")

    assert response.status_code == 404
