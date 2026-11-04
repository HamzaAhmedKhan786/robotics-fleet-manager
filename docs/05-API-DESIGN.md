
# REST and WebSocket API Design

## 1. API Conventions

Base path: `/api/v1`

All JSON responses use UTF-8.

Authentication is required for protected operations.

Errors use a consistent structure:

```json
{
  "error": {
    "code": "ROBOT_NOT_AVAILABLE",
    "message": "The selected robot is unavailable"
  }
}
```

## 2. Robot Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | /robots | List robots |
| POST | /robots | Register robot |
| GET | /robots/{id} | Robot details |
| GET | /robots/{id}/telemetry | Latest telemetry |
| GET | /robots/{id}/missions | Robot mission history |

Example robot registration:

```json
{
  "name": "AMR-001",
  "type": "warehouse_amr",
  "capabilities": ["transport"],
  "max_payload_kg": 100
}
```

## 3. Mission Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| POST | /missions | Create mission |
| GET | /missions | List missions |
| GET | /missions/{id} | Mission details |
| POST | /missions/{id}/cancel | Request cancellation |
| GET | /missions/{id}/events | Mission history |

Example mission creation:

```json
{
  "pickup": {"x": 2, "y": 4},
  "destination": {"x": 12, "y": 8},
  "priority": 2,
  "required_capabilities": ["transport"]
}
```

## 4. Fleet Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | /fleet/summary | Fleet statistics |
| GET | /fleet/alerts | Operational alerts |
| GET | /health | Application health |
| GET | /ready | Dependency readiness |

## 5. WebSocket

Endpoint: `/api/v1/ws/fleet`

Example message:

```json
{
  "event": "robot.telemetry.updated",
  "timestamp": "2026-11-04T18:00:00Z",
  "data": {
    "robot_id": "robot-001",
    "battery_percent": 76,
    "position": {"x": 5, "y": 7},
    "status": "MOVING"
  }
}
```

## 6. Security

- Authentication for protected endpoints
- Role-based authorization
- Input validation
- Request size limits
- Rate limiting where appropriate
- Audit logging
- WebSocket authentication

## 7. API Documentation

FastAPI will generate OpenAPI documentation at `/docs` and `/openapi.json` when the backend is implemented.
