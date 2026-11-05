"""Integration tests for robot API endpoints."""


async def test_register_robot(client):
    response = await client.post(
        "/api/v1/robots",
        json={
            "name": "AMR-001",
            "battery_level": 85,
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["name"] == "AMR-001"
    assert data["battery_level"] == 85
    assert data["status"] == "offline"
    assert "id" in data


async def test_list_robots(client):
    await client.post(
        "/api/v1/robots",
        json={"name": "AMR-001", "battery_level": 85},
    )

    response = await client.get("/api/v1/robots")

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["name"] == "AMR-001"


async def test_get_robot_by_id(client):
    created = await client.post(
        "/api/v1/robots",
        json={"name": "AMR-001", "battery_level": 85},
    )

    robot_id = created.json()["id"]

    response = await client.get(f"/api/v1/robots/{robot_id}")

    assert response.status_code == 200
    assert response.json()["id"] == robot_id


async def test_duplicate_robot_name(client):
    payload = {
        "name": "AMR-001",
        "battery_level": 85,
    }

    first = await client.post("/api/v1/robots", json=payload)
    second = await client.post("/api/v1/robots", json=payload)

    assert first.status_code == 201
    assert second.status_code == 409


async def test_invalid_battery_level(client):
    response = await client.post(
        "/api/v1/robots",
        json={
            "name": "AMR-002",
            "battery_level": 150,
        },
    )

    assert response.status_code == 422


async def test_robot_not_found(client):
    response = await client.get("/api/v1/robots/00000000-0000-0000-0000-000000000001")

    assert response.status_code == 404
