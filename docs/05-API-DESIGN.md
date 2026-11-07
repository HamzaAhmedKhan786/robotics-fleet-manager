# API Design — FleetOS

## 1. API conventions

Base prefix: `/api/v1` for fleet resources. JSON over HTTP; FastAPI OpenAPI explorer at `/docs`. Authentication and standardized domain error bodies are **planned**; do not claim endpoints are secured. HTTP 409 is appropriate for state conflicts/capacity errors, 422 for validation. Check current OpenAPI for exact request/response and status codes.

## 2. Current endpoints

| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | API process health, not full dependency readiness |
| GET | `/api/v1/robots` | List persisted robots |
| POST | `/api/v1/robots` | Register robot manually |
| PATCH | `/api/v1/robots/{robot_id}` | Update permitted robot state/properties |
| GET | `/api/v1/missions` | List missions |
| POST | `/api/v1/missions` | Queue mission for autonomous dispatch |
| POST | `/api/v1/missions/{mission_id}/assign` | Administrative/manual lifecycle endpoint (if enabled) |
| POST | `/api/v1/missions/{mission_id}/start` | Administrative/manual lifecycle endpoint (if enabled) |
| POST | `/api/v1/missions/{mission_id}/complete` | Administrative/manual lifecycle endpoint (if enabled) |
| POST | `/api/v1/missions/{mission_id}/cancel` | Cancel eligible mission |
| GET | `/api/v1/fleet/summary` | Robot and mission counts |
| GET | `/api/v1/fleet/warehouse` | Warehouse stations and weighted edges |
| POST | `/api/v1/demo/simulation` | Queue two missions; **never create robots** |
| GET | `/api/v1/system/dispatcher` | Local worker-status diagnostic, if enabled |

Not all handler names or optional endpoints are asserted as stable: the live OpenAPI document is authoritative for the current checkout.

## 3. Example create mission

```json
{
  "pickup_location": "STATION-A2",
  "delivery_location": "STATION-B1",
  "priority": 4
}
```

A new mission begins pending. The background worker will assign it if route/battery constraints allow; otherwise it stays queued.

## 4. Example register robot

```json
{
  "name": "AMR-005",
  "battery_level": 85,
  "current_location": "STATION-A1"
}
```

Registration is operator-initiated and should check `fleet_size < 15` atomically. The current UX starts newly registered robots offline; the operator may later activate an eligible robot.

## 5. Mission response fields

UUID; pickup/delivery; priority; status; assigned robot UUID or null; timestamps; optional `plan` and `selection_reason`. Plan contains path, pickup/delivery/total distances, battery estimate, safety reserve, duration and feasibility. Fields/precision should be checked against the current Pydantic schema.

## 6. Demo API

`POST /api/v1/demo/simulation`: creates two missions, returns their IDs and `robots_created: 0`. Any legacy `auto_provision: true` should be rejected by the revised implementation. Local-only protection is **not** a substitute for real authentication.

## 7. Planned telemetry APIs (Option B)

```json
{
  "robot_id": "<uuid>",
  "mission_id": "<uuid>",
  "position": {"x": -4.2, "z": 3.1},
  "segment_index": 1,
  "progress_percent": 42.5,
  "recorded_at": "<UTC timestamp>"
}
```

Future endpoint: `GET /api/v1/fleet/telemetry` or an authenticated WebSocket/SSE stream. Not implemented. Movement state must originate from the Rust/Python backend, not frontend clocks.

## 8. Future hardening

Operator authentication, role-based writes, rate limiting, command idempotency keys, audit events, request size limits and structured errors.

---

## Original specification retained for traceability (historical baseline)

> **Historical reference, not a statement of current implementation.** The original text below is preserved so that no early requirement, design option, setup explanation, or proposed feature is lost. Where it differs from the current sections above, **the current sections take precedence**. In particular, references to Next.js, 20 robots, WebSocket telemetry, continuous movement, Redis integration, A* navigation, authentication, or physical control may describe earlier proposals rather than implemented behavior. Review original setup commands against the current repository before running them.

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
