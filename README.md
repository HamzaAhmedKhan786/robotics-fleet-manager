# FleetOS — Robotics Fleet Manager

**Open-source autonomous mobile robot (AMR) fleet orchestration and warehouse simulation platform, built with Python, Rust, PostgreSQL, React, and Three.js.**

> **Project status — Functional local prototype / actively developed (7 November 2026).** The REST backend, persistent robot and mission records, deterministic mission assignment, simulation worker, and 2D/3D operator dashboard are implemented. This is **not a production-ready or safety-certified robot-control system**. The frontend estimates cart motion from mission timing; backend-authoritative coordinates, collision prevention, streaming telemetry, authentication, and physical robot adapters remain planned.

## Table of contents

- [Overview](#overview)
- [Project classification](#project-classification)
- [FleetOS dashboard](#fleetos-dashboard)
- [Current capabilities — implemented](#current-capabilities--implemented)
- [Technology stack](#technology-stack)
- [Current architecture and responsibilities](#current-architecture-and-responsibilities)
- [Repository structure — actual current files](#repository-structure--actual-current-files)
- [Getting started — Windows PowerShell](#getting-started--windows-powershell)
- [Development infrastructure](#development-infrastructure)
- [API and simulation workflow](#api-and-simulation-workflow)
- [Testing and code quality](#testing-and-code-quality)
- [Implementation status](#implementation-status)
- [Planned — not yet implemented](#planned--not-yet-implemented)
- [Development roadmap](#development-roadmap)
- [Documentation](#documentation)
- [Contributing](#contributing)
- [Safety disclaimer](#safety-disclaimer)
- [License](#license)

## Overview

Robotics Fleet Manager (FleetOS) explores how simulated autonomous mobile robots can be coordinated in warehouses, logistics centers, and industrial facilities. It provides an operator command center, persistent fleet and mission state, automatic dispatch, planned station-to-station paths, and a 3D warehouse visualization.

The platform's objectives are to:

- Assign and manage warehouse pickup/delivery missions.
- Monitor robot availability, battery, current station, and operating state.
- Schedule jobs according to operational constraints, priorities, battery feasibility, and travel distance.
- Coordinate shared warehouse resources and recover from interruptions (**future extensions**).
- Simulate robot behavior before any physical deployment.
- Expose a modular base for Rust robotics logic and optional AI-assisted operations.

**Current scope:** six named warehouse stations (`STATION-A1` through `STATION-B3`), simulated AMR carts, and a **maximum 15-robot design policy**. Operators manually register robots; **the demo creates missions, never robots**. If no eligible robot is available, jobs stay pending instead of adding robots. Verify full concurrency enforcement of the 15-robot cap before describing it as production-enforced.

**Not in the current scope:** live physical-robot telemetry, real-world navigation, guaranteed collision avoidance, and safety-critical robot control. The original broader specification is retained under [Planned — not yet implemented](#planned--not-yet-implemented).

## Project classification

- Robotics and Autonomous Systems
- Distributed Systems and Fleet Orchestration
- Mission Scheduling and Operations Research
- Warehouse Digital Twin and Simulation
- Real-Time Monitoring (poll-based prototype; streaming planned)
- Optional Agentic AI and Multi-Agent Systems (planned)

## FleetOS dashboard

### Interactive 3D warehouse digital twin

![FleetOS 3D warehouse and robot carts](docs/Assets/OverviewBotFleetManagement.png)

The React Three Fiber scene includes racks, stations, floor grid, 3D AMR carts, battery/status labels, colored active mission routes, selectable robots, and camera orbit/zoom/pan. A toggle switches between the 3D scene and the 2D network view.

**Simulation truthfulness:** current cart motion is browser-side interpolation based on a mission's `started_at`, route and planned `duration_seconds`. It is a **visual estimate**, not position telemetry persisted in PostgreSQL. Backend-authoritative movement is the next engineering milestone.

### Robot fleet management

![FleetOS robot fleet overview](docs/Assets/RobotFleetStatus.png)

Operators can register robots manually and view their operating states (`offline`, `available`, `busy`, `charging`, `error`), battery levels, known station, and mission association. The dashboard provides per-robot details and filtering. Manually registered robots start offline and can be activated when eligible.

### Mission management

![FleetOS mission management](docs/Assets/MissionManagement.png)

Operators can create pickup/delivery missions, set priorities, inspect the mission queue, view scheduler explanations and planned routes, and review completed mission history. The autonomous worker dispatches and progresses eligible jobs. Ineligible work remains pending.

## Current capabilities — implemented

| Area | Implementation | Important limitation |
|---|---|---|
| Fleet registry | PostgreSQL-backed robot records, registration, statuses, battery and current station | No hardware telemetry feed |
| Mission lifecycle | Persistent jobs with `pending`, `assigned`, `in_progress`, `completed`, `cancelled`, `failed` | Recovery and audit-event stream not yet complete |
| Automated dispatch | Async worker retries pending missions and advances mission execution | Time-based simulated progression |
| Scheduling | Python graph/energy checks and native Rust candidate selection via PyO3 | Advanced routing and movement remain Python/browser-side |
| Routing | Shortest paths over current six-station warehouse graph | No traffic reservations or dynamic obstacles |
| 3D digital twin | React, Three.js, React Three Fiber, Drei | Frontend-timed animation, not authoritative robot coordinates |
| 2D network | Station graph, selected routes and mission overlays | Not live robot tracking |
| Data persistence | Async SQLAlchemy, asyncpg, PostgreSQL, Alembic revisions | Not a telemetry time-series model yet |
| Local monitoring | Health endpoint, fleet summary, status cards and REST polling | No confirmed WebSocket event stream |
| Tests | Unit/integration test files and developer commands | Run tests locally; no claim of a current passing count |

### Current fleet policy

1. Maximum target fleet size is **15 registered robots**.
2. Robots are registered **only by an operator/manual API action**, not automatically when demo jobs run.
3. The demo action creates **two missions** against existing fleet capacity.
4. If eligible robots are unavailable, missions stay `pending` and are retried.
5. One robot should not be assigned multiple active missions simultaneously; assignment concurrency needs continued testing.

## Technology stack

| Layer | Current choice | Status |
|---|---|---|
| Web UI | React + TypeScript + Vite | Implemented |
| 3D scene | Three.js + React Three Fiber + Drei | Implemented |
| Backend | Python 3.12, FastAPI, Pydantic | Implemented |
| Environment | Pixi, `pixi.toml`, `pixi.lock` | Implemented |
| Persistence | PostgreSQL, SQLAlchemy async, Alembic, asyncpg | Implemented |
| Native scheduling | Rust, PyO3, Maturin (`crates/fleet-scheduler/`) | Implemented initial candidate selector |
| Background processing | Python asyncio worker | Implemented |
| UI updates | REST requests/polling (configured around 2 seconds) | Implemented |
| Cache / transient coordination | Redis | Planned / optional |
| Event push | WebSockets | Planned |
| Robot integration | ROS 2, MQTT, vendor adapters | Future |
| Development infrastructure | Native Windows PostgreSQL; Docker Compose available | Hybrid local environment |
| Test and lint | Pytest, Ruff, Pyright, TypeScript build | Code and commands available |
| Browser E2E | Playwright | Planned / not verified |
| CI/CD | GitHub Actions | Planned / not verified |

**Recorded architecture decision:** The early design proposed **Next.js**; the working frontend now uses **React + Vite**. This is a conscious implementation choice, not a requirement deletion. See [ADR 0001](docs/ADR/0001-TECHNOLOGY-STACK.md).

## Current architecture and responsibilities

```mermaid
flowchart TD
    Operator["Operator"] --> UI["React / TypeScript / Vite Dashboard"]
    UI -->|REST polling| API["FastAPI REST Backend"]
    API --> Models["Fleet + Mission Services"]
    Models --> PG[("PostgreSQL")]
    Worker["Python Autonomous Worker"] --> Models
    Worker --> Route["Python Warehouse Graph / Route / Energy Checks"]
    Worker --> Native["Rust Scheduler via PyO3"]
    API --> Status["Warehouse / Fleet Summary"]
    UI --> Twin["Three.js 2D / 3D Visualization"]
    FutureMovement["Planned: Rust Movement Engine + Persisted Coordinates"] -.-> Worker
    FutureStreaming["Planned: WebSockets / Redis"] -.-> API
    FutureAI["Planned: Operations AI Agents"] -.-> API
    FutureROS["Future: ROS 2 / MQTT Hardware Adapters"] -.-> API
```

### Architectural responsibilities

**FastAPI backend.** Implements REST APIs, validates inputs, and manages persistence-backed robot/mission operations. Backend API routes are in `apps/backend/api/`; configuration and database sessions are separated into `core/` and `db/`.

**Fleet orchestration core.** Coordinates robot registration, state updates, assignment, mission transitions, priority and automatic worker progression. Services live in `apps/backend/services/`.

**Rust mission scheduler.** The currently integrated native Rust extension selects a candidate deterministically from prequalified robots. The current Python orchestration handles route and battery-feasibility checks. Rust routing, per-tick kinematics, and traffic calculations are **next-phase work**, not features currently implemented.

**Warehouse graph and route planning.** The backend provides the current six-station topology and calculates graph paths. The 2D frontend can independently visualize shortest paths; its drawing must not be mistaken for movement telemetry.

**Autonomous worker.** `scripts/auto_worker.py` checks pending and assigned missions, dispatches when possible, and finishes in-progress jobs according to simulated mission timing. If integrated into the FastAPI lifespan, do **not** also start a second worker process. Multiple production API workers require an explicit singleton/leader or external job-runner design.

**Robot state management.** Persists station-based location, battery and operating states. Continuous coordinates, heading, velocities, heartbeat telemetry and execution progress are **planned**.

**PostgreSQL.** Authoritative store for currently implemented robot and mission records. Mission telemetry/event history tables from the original design are future additions where not present in current migrations.

**Traffic coordinator.** **Planned:** reservation of shared aisles, conflict detection, restricted zones, and deadlock prevention. Do not describe it as implemented.

**Redis.** **Planned/optional:** temporary coordination, caching and pub/sub. The core prototype should work without a Redis container; persistent mission state belongs in PostgreSQL.

**Robot simulator / digital twin.** The current worker performs time-based mission lifecycle simulation and the browser estimates position along a path. Full backend-authoritative movement, battery-per-tick updates and fault injection are planned.

**Physical robot adapters.** **Future:** ROS 2/MQTT/vendor APIs, acknowledgements, telemetry and hardware-independent command interfaces. Real robots must retain their own motion and emergency-stop safeguards.

## Repository structure — actual current files

The following is reconstructed from `project-structure-current.txt` supplied on **7 November 2026**. It contains tracked and non-ignored untracked paths, not ignored generated artifacts, and is **not** an invented future layout.

```text
robotics-fleet-manager/
├── alembic/
│   ├── versions/
│   │   ├── 0a70761fc704_create_robots_table.py
│   │   ├── 8f74e2cbf143_add_robot_current_location.py
│   │   ├── b4f2c9d10e11_add_mission_execution_plan.py
│   │   └── d7e548af6cab_create_missions_table.py
│   ├── env.py
│   ├── README
│   └── script.py.mako
├── apps/
│   ├── backend/
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── demo.py
│   │   │   ├── fleet.py
│   │   │   ├── missions.py
│   │   │   └── robots.py
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   └── config.py
│   │   ├── db/
│   │   │   ├── __init__.py
│   │   │   ├── base.py
│   │   │   └── session.py
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── mission.py
│   │   │   └── robot.py
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── mission.py
│   │   │   └── robot.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── assignment_service.py
│   │   │   ├── mission_service.py
│   │   │   ├── robot_service.py
│   │   │   ├── route_planner.py
│   │   │   ├── scheduling_service.py
│   │   │   └── warehouse_graph.py
│   │   ├── __init__.py
│   │   └── main.py
│   └── __init__.py
├── crates/
│   └── fleet-scheduler/
│       ├── src/
│       │   └── lib.rs
│       ├── Cargo.lock
│       └── Cargo.toml
├── docs/
│   ├── ADR/
│   │   ├── 0001-TECHNOLOGY-STACK.md
│   │   └── 0002-LOCAL-DEVELOPMENT-INFRASTRUCTURE.md
│   ├── Assets/
│   │   ├── MissionManagement.png
│   │   ├── OverviewBotFleetManagement.png
│   │   └── RobotFleetStatus.png
│   ├── 01-Project-Overview.md
│   ├── 02-REQUIREMENTS.md
│   ├── 03-ARCHITECTURE.md
│   ├── 04-SYSTEM-DESIGN.md
│   ├── 05-API-DESIGN.md
│   ├── 06-DATABASE-DESIGN.md
│   ├── 07-ROBOT-SIMULATION.md
│   ├── 08-MISSION-SCHEDULING.md
│   ├── 09-SAFETY-AND-SECURITY.md
│   ├── 10-TESTING-STRATEGY.md
│   ├── 11-DEPLOYMENT.md
│   └── 12-DEVELOPMENT-ROADMAP.md
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── RobotCart3D.tsx
│   │   │   ├── RobotDetailsPanel.tsx
│   │   │   ├── RobotFleetView.tsx
│   │   │   ├── Station3D.tsx
│   │   │   └── Warehouse3D.tsx
│   │   ├── api.ts
│   │   ├── App.tsx
│   │   ├── main.tsx
│   │   ├── styles.css
│   │   ├── types.ts
│   │   └── vite-env.d.ts
│   ├── index.html
│   ├── package-lock.json
│   ├── package.json
│   ├── README.md
│   ├── tsconfig.json
│   └── vite.config.ts
├── scripts/
│   ├── auto_worker.py
│   ├── seed_demo.py
│   ├── test_rust_scheduler.py
│   └── test_sqlalchemy_connection.py
├── tests/
│   ├── integration/
│   │   ├── __init__.py
│   │   ├── test_assignment_api.py
│   │   ├── test_mission_api.py
│   │   └── test_robot_api.py
│   ├── unit/
│   │   ├── test_database_scheduling.py
│   │   ├── test_route_planner.py
│   │   ├── test_scheduling_service.py
│   │   └── test_warehouse_graph.py
│   ├── __init__.py
│   └── conftest.py
├── typings/
│   └── fleet_scheduler/
│       └── __init__.pyi
├── .gitattributes
├── .gitignore
├── alembic.ini
├── compose.yaml
├── CONTRIBUTING.md
├── LICENSE
├── pixi.lock
├── pixi.toml
├── project-structure.txt
├── pyrightconfig.json
├── pytest.ini
├── README.md
├── requirements.txt
└── test_db_connection.py
```

Important paths: `frontend/` is the **real frontend root**, `apps/backend/` is the FastAPI service, `crates/fleet-scheduler/` is the Rust module, `scripts/auto_worker.py` is the simulation worker, `alembic/versions/` stores schema migrations, and `tests/` contains Python unit and integration tests. The older plan mentioned `apps/frontend/`, `services/robot-simulator/`, `packages/shared-schemas/` and `infrastructure/docker/`; these are **not present in the supplied current file list**. They are design history or potential future layout, not files you should create simply to satisfy old documentation.

## Getting started — Windows PowerShell

### Prerequisites

The main local development setup uses:

- Windows 11 and PowerShell (or another compatible shell).
- Git and [Pixi](https://pixi.sh/) to manage the Python 3.12 environment.
- Node.js LTS and npm for the React/Vite frontend.
- Rust toolchain (`cargo` and `rustc`) and Maturin/PyO3 integration for the Rust extension, according to `pixi.toml`.
- PostgreSQL 18 running as a **native Windows service** (the existing development decision).
- Docker Desktop **only if needed** for optional Redis or alternative containerized infrastructure.

Do not assume the Python runtime must also be installed system-wide; Pixi manages the environment. The existing `pixi.lock` is the reproducible dependency baseline.

### 1. Clone the repository

```powershell
git clone https://github.com/HamzaAhmedKhan786/robotics-fleet-manager.git
cd robotics-fleet-manager
```

For the existing local checkout:

```powershell
Set-Location 'C:\Users\DELL\Documents\Projects\Robotics & Autonomous Systems\robotics-fleet-manager'
```

PowerShell's `&` in this path requires quoting when the path is used in commands.

### 2. Install Python dependencies and verify toolchain

```powershell
pixi install
pixi run python --version
rustc --version
cargo --version
```

Expected Python runtime is **3.12.x**. The Rust extension must be built/installed using the existing Pixi/Maturin development configuration when required; don't assume `cargo build` alone installs it into Python. A helper is present at `scripts/test_rust_scheduler.py` to check import/integration after installation.

### 3. Configure environment variables

Create `.env` only if it is missing. **Your latest supplied file list does not show `.env.example`**, so first check whether it exists in your working checkout:

```powershell
if (Test-Path .env.example) {
    if (-not (Test-Path .env)) { Copy-Item .env.example .env }
} else {
    Write-Host "No .env.example found. Create .env locally using the configuration keys in apps/backend/core/config.py."
}
```

**Do not overwrite your configured `.env`.** Inspect `apps/backend/core/config.py` for authoritative supported keys; use `.env.example` only if your checkout contains one. Example values (placeholders only, **not** live credentials):

```dotenv
APP_NAME=Robotics Fleet Manager
APP_ENV=development
LOG_LEVEL=INFO

POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=robotics_fleet
POSTGRES_USER=postgres
POSTGRES_PASSWORD=CHANGE_ME
DATABASE_URL=postgresql+asyncpg://postgres:CHANGE_ME@localhost:5432/robotics_fleet

SIMULATION_ENABLED=true

# Optional future integrations — configure only when implemented/used:
REDIS_URL=redis://localhost:6379/0
# JWT_SECRET=GENERATE_A_UNIQUE_RANDOM_SECRET
# JWT_ALGORITHM=HS256
```

`DATABASE_URL` credentials with reserved URL characters need proper percent encoding. Use separate database settings for local testing as defined in `tests/conftest.py`; do **not** point test fixtures at your development database.

If/when JWT authentication is implemented, generate a secret locally rather than copying the placeholder:

```powershell
pixi run python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Never commit `.env`, private keys, tokens, production credentials or database dumps with sensitive content.

### 4. PostgreSQL setup and verification

**Check the native service:**

```powershell
Get-Service *postgres*
Get-NetTCPConnection -LocalPort 5432 -State Listen -ErrorAction SilentlyContinue
```

**Connect using the PostgreSQL 18 CLI:**

```powershell
& 'C:\Program Files\PostgreSQL\18\bin\psql.exe' -U postgres -h localhost -p 5432 -d postgres
```

Create the application database *only if it does not exist*:

```sql
CREATE DATABASE robotics_fleet;
```

Useful interactive `psql` commands:

```text
\l
\c robotics_fleet
\dt
\q
```

Use a dedicated least-privilege application role for staging/production; the local administrative `postgres` role is not a production recommendation.

### 5. Database migrations

From the repository root, with PostgreSQL running and `.env` configured:

```powershell
pixi run alembic upgrade head
pixi run alembic current
```

The repository contains versioned migrations for robots, current station and missions/execution plans. Do not hand-create production tables or edit applied migrations; add new migrations for new fields such as continuous robot coordinates.

### 6. Start the backend

Open a PowerShell terminal in the repository root:

```powershell
pixi run backend
```

Local endpoints:

- FastAPI OpenAPI UI: <http://127.0.0.1:8000/docs>
- OpenAPI JSON: <http://127.0.0.1:8000/openapi.json>
- Health: <http://127.0.0.1:8000/health>
- Fleet summary: <http://127.0.0.1:8000/api/v1/fleet/summary>
- Warehouse network: <http://127.0.0.1:8000/api/v1/fleet/warehouse>
- Robots: <http://127.0.0.1:8000/api/v1/robots>
- Missions: <http://127.0.0.1:8000/api/v1/missions>

The fleet summary is backed by live persisted application state, **not the old README's placeholder zeros**.

### 7. Autonomous worker: choose ONE mode

The project includes `scripts/auto_worker.py`. Depending on your current `apps/backend/main.py` wiring, the worker can be started as part of the FastAPI lifespan or separately.

**Mode A — worker is already started by the API lifespan:** keep `pixi run backend` running; **do not** launch another worker.

**Mode B — no worker running in the API lifespan:** start it in one additional terminal:

```powershell
pixi run python -m scripts.auto_worker
```

Confirm the current startup wiring in `apps/backend/main.py` before choosing. Running both simultaneously can cause duplicate dispatch attempts or conflicting simulated mission updates. A production deployment will need dedicated worker ownership and reliability controls.

### 8. Start the React/Vite frontend

Open a separate terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open <http://127.0.0.1:5173/overview> (or the Vite address printed in the terminal). The frontend files live in `frontend/`, **not** `apps/frontend/`.

For production-bundle compilation:

```powershell
npm run build
```

The existing `frontend/package.json` should invoke Vite and TypeScript with direct Node paths where necessary for the Windows project directory containing `&`.

### 9. Basic local walkthrough

1. Confirm PostgreSQL, the FastAPI server and the React frontend are running.
2. Add a robot manually under **Robot Fleet** (new robots start offline).
3. Activate the robot if its state and battery satisfy eligibility conditions.
4. Create a pickup/delivery mission, or run the demo to create **two missions without creating robots**.
5. Observe queued/assigned/in-progress/completed states and inspect scheduler explanation in **Mission Operations**.
6. Switch between **3D Warehouse** and **2D Network**; select a robot and inspect its status.
7. If no robot is eligible, ensure the job remains queued and does not trigger robot auto-provisioning.

Do not use the front-end cart animation as proof of exact robot localization; this remains a planned backend simulation feature.

## Development infrastructure

### Primary hybrid Windows setup

This deliberately minimizes local resource overhead. See [ADR 0002](docs/ADR/0002-LOCAL-DEVELOPMENT-INFRASTRUCTURE.md).

| Component | Location | Default address / role |
|---|---|---|
| FastAPI | Windows / Pixi | `127.0.0.1:8000` |
| PostgreSQL 18 | Native Windows service | `localhost:5432` |
| React/Vite | Windows / Node.js | Vite development port, typically `5173` |
| Rust scheduler | Native PyO3 extension | Imported by Python |
| Autonomous worker | Python process or API lifespan | Single active dispatcher |
| Redis | Docker container **if introduced** | `localhost:6379` (optional/planned) |

### Redis setup — planned/optional

The original project design included Redis for transient coordination, caching and event distribution. **Redis has not been abandoned**, but it is not a dependency of the currently demonstrated REST-polling workflow.

If the Compose file defines a `redis` service and Docker Desktop is available:

```powershell
docker compose up -d redis
docker compose ps
docker compose exec redis redis-cli ping
```

Expected `redis-cli ping` output when running successfully:

```text
PONG
```

Stop it when not required:

```powershell
docker compose stop redis
```

**Avoid starting `docker compose up -d` indiscriminately** when native PostgreSQL already occupies port 5432: an additional PostgreSQL container can conflict with the Windows service. Redis application wiring and its tests remain future work.

### Full Docker infrastructure — alternative

The repository retains `compose.yaml`. A fully containerized database/Redis stack is an alternative where local native PostgreSQL is not used. Backend/frontend application containers, backups, deployment pipelines, production credentials and readiness checks need to be designed and verified separately.

## API and simulation workflow

### Current API conventions

- Root health endpoint: `GET /health`.
- API base: `/api/v1`.
- Robots: `GET /api/v1/robots`, registration and status updates under the robots router.
- Missions: `GET /api/v1/missions`, mission creation and lifecycle actions under the missions router.
- Fleet: `GET /api/v1/fleet/summary`, `GET /api/v1/fleet/warehouse`.
- Demo: mission-only creation under the demo router.
- **FastAPI's `/docs` and `/openapi.json` are the authoritative current endpoint/field reference.** Do not treat conceptual endpoints in the older API-design specification as implemented unless `/docs` confirms them.

### Mission lifecycle

```mermaid
stateDiagram-v2
    [*] --> pending
    pending --> assigned: eligible robot found
    assigned --> in_progress: worker starts job
    in_progress --> completed: simulated duration elapsed
    pending --> cancelled
    assigned --> cancelled
    pending --> failed: validated failure path
    assigned --> failed: validated failure path
    in_progress --> failed: validated failure path
```

Supported transitions depend on backend service validation. The diagram shows the conceptual state progression; it does **not** imply every listed failure transition is already implemented.

### Scheduling logic today

1. Select pending missions, respecting their queue priority.
2. Find available robot candidates and examine current station and battery.
3. Calculate warehouse shortest routes and simulated energy requirements in Python.
4. Pass eligible candidates to the native Rust selection function; select deterministically using distance and battery tie-breakers.
5. Persist robot assignment and mission plan; allow the worker to start eligible assigned missions.
6. Complete jobs when their simulated duration has elapsed, update status and apply the modeled battery effect.
7. When there is no suitable robot, leave the mission pending for the next worker cycle.

**Not yet delivered:** Rust per-tick movement/traffic engine, actual robot telemetry, idempotent hardware commands, collision-safe navigation, comprehensive fault recovery.

### Warehouse topology

The current six stations are `STATION-A1`, `STATION-A2`, `STATION-A3`, `STATION-B1`, `STATION-B2`, `STATION-B3`. The graph and edge distances are in `apps/backend/services/warehouse_graph.py`; station positions for visualization live in the frontend 3D/2D components. Current paths are **topological and simulated**, not validated real-world driving paths.

## Testing and code quality

Run checks from the repository root with a configured **separate test database**. Tests may write and roll back test records; do not target production or development data accidentally.

```powershell
pixi run ruff check apps tests scripts alembic
pixi run pyright apps/backend
pixi run pytest tests -q --tb=short
```

Build the frontend:

```powershell
cd frontend
npm run build
cd ..
```

Additional relevant scripts:

```powershell
pixi run python scripts/test_rust_scheduler.py
pixi run python scripts/test_sqlalchemy_connection.py
```

Run these only with the appropriate local services and native extension available. Unit and integration tests currently live under `tests/unit/` and `tests/integration/`. The original testing design additionally specified Playwright E2E tests, failure injection, performance benchmarks, security testing and CI; these remain **planned**, not silently discarded.

## Implementation status

| Feature | State as of 2026-11-07 | Notes |
|---|---|---|
| Git, Pixi, Python environment | Implemented | Current repository contains project configuration and lockfile |
| Native PostgreSQL 18 connectivity | Implemented locally | Hybrid Windows development decision |
| SQLAlchemy and Alembic | Implemented | Current migrations present |
| Robot registration, states and battery | Implemented | Registration policy needs concurrency verification |
| Mission management and DB persistence | Implemented | Current mission lifecycle represented in model/API |
| Six-station graph routing | Implemented | Python pathfinding/topology |
| Native Rust scheduler integration | Implemented (initial scope) | Candidate selection via PyO3 |
| Autonomous worker | Implemented | Timed dispatch/mission progression |
| React/TypeScript UI | Implemented | Overview, Robots, Missions |
| 2D route network | Implemented | Graph view |
| 3D warehouse and AMR models | Implemented | Visualization |
| Mission-timed visual cart movement | Implemented | Browser estimate, not telemetry |
| Max 15 robots / demo without auto-provisioning | Agreed policy; verify | Inspect and test every registration route |
| Backend per-tick robot coordinates | **Planned** | Option B |
| Rust movement and traffic engine | **Planned** | Option B and later traffic phase |
| Robot heartbeats and full telemetry history | **Planned** | Not evident in current migrations |
| Robot capabilities and payload model | **Planned** | Original requirements retained |
| Event/audit trail | **Planned** | Original database design retained |
| Redis, WebSocket streaming | **Planned / optional** | Current UI uses polling |
| Authentication / RBAC | **Planned** | Do not expose current prototype publicly |
| ROS 2 / MQTT adapters | **Future** | No physical robot control |
| Containerized production deployment | **Planned** | Local demo only |
| GitHub Actions and Playwright | **Planned / unverified** | No completion claim from directory list |

## Planned — not yet implemented

The following are **retained project requirements and expansion plans**, not working current features. They are not cancelled or omitted merely because the initial implementation took a simpler route.

### 1. Option B — Rust-powered backend-authoritative movement (next milestone)

- Move graph routing and energy-calculation kernels to Rust where appropriate.
- Implement deterministic per-tick route progress, coordinate updates, speed, heading, and battery consumption.
- Add coordinate and mission-progress persistence through new Alembic revisions.
- Update the Python worker to call Rust and commit simulation state transactionally.
- Expose stable robot progress/positions through FastAPI.
- Interpolate between **backend-observed** positions in React Three Fiber rather than estimating progress solely from `started_at`.
- Test route completion, restart/recovery, invalid paths, concurrency and battery limits.

### 2. Traffic coordination and multi-robot reliability

- Shared-path or aisle reservations, restricted warehouse zones and conflict detection.
- Multi-robot path planning, dynamic obstacles, congestion awareness and safe waiting.
- Atomic reservations, duplicate-command safety, idempotency and command acknowledgements.
- Offline/heartbeat timeouts, blocked paths, mission interruption and recovery workflows.
- Operational event history, retries, telemetry retention and auditability.

### 3. Event streaming and observability

- WebSockets for backend-to-dashboard event delivery.
- Optional Redis for caching, transient coordination and pub/sub when warranted.
- Time-stamped telemetry, structured logs, metrics, alerts and dependency-readiness probes.
- Performance evaluation for the **15-robot** current policy; prior 20-robot figures were exploratory engineering targets, not the agreed current limit.

### 4. Agentic AI and assisted operations

- Natural-language mission creation/planning and operational summaries.
- Fleet Supervisor/Diagnostic Agent and mission explanations.
- Optional cloud LLM and/or local provider such as Ollama.
- Tool permissions, audit logs and operator approval for sensitive actions.
- Deterministic scheduling and robotics safety checks remain authoritative; AI cannot bypass them.

### 5. Security and production engineering

- Authentication, RBAC (administrator/operator/viewer), API authorization, input/rate limits.
- Production secrets, TLS, scoped database credentials, security logs and vulnerability scanning.
- GitHub Actions lint/type/test/build workflows, optional browser E2E tests, staging deploys, monitoring and backups.
- Worker ownership/leader election and multi-process failure recovery before scaling the API.

### 6. Physical robotics and longer-term research

- ROS 2/MQTT/vendor-specific robot adapters with acknowledgements and telemetry mapping.
- Hardware-independent control interfaces and simulation-to-physical compatibility tests.
- Robot-local protective stopping, obstacle avoidance, emergency stop and formal safety assessment.
- Batch scheduling, constraint optimization, multi-agent pathfinding, predictive maintenance and multi-site orchestration.

### 7. Original design elements preserved for future evaluation

The initial proposal included a standalone Python simulator, capabilities, payload types, robot telemetry/events tables, planned folder modules such as `services/robot-simulator/`, `packages/shared-schemas/`, and `infrastructure/docker/`. These have **not been implemented in the current tree**. Retain their intent in the design specifications and revisit if they become useful, rather than creating empty placeholder directories or claiming they currently exist.

## Development roadmap

### Phase 1 — Repository and environment

- [x] Create repository and project documentation.
- [x] Configure Pixi/Python and FastAPI.
- [x] Set up native PostgreSQL and connectivity.
- [x] Add SQLAlchemy models and Alembic migrations.
- [ ] Verify optional Redis service/integration when needed.

### Phase 2 — Fleet and mission core

- [x] Implement robot registration and statuses.
- [x] Implement mission creation and lifecycle.
- [x] Implement initial deterministic Rust robot candidate selector.
- [x] Implement Python warehouse path and battery checks.
- [x] Implement autonomous worker for simulation-time mission completion.
- [ ] Validate maximum-15 registration cap under concurrency, worker singleton behavior and wider recovery cases.

### Phase 3 — Operator dashboard and digital twin

- [x] Build React/Vite FleetOS command center.
- [x] Implement Robot Fleet and Mission Operations interfaces.
- [x] Add 2D station network and interactive 3D warehouse.
- [x] Add AMR carts, shelves, colored routes and status details.
- [x] Add current frontend mission-time visualization.

### Phase 4 — Rust movement engine (next)

- [ ] Add native route/energy and motion-step APIs.
- [ ] Extend persistence with coordinates, heading and movement progress.
- [ ] Integrate worker updates and API telemetry.
- [ ] Animate carts from backend state.
- [ ] Test timing, battery, retries and consistency.

### Phase 5 — Traffic, failure recovery and streaming

- [ ] Add corridor reservation and collision-conflict checks.
- [ ] Introduce fault injection, heartbeat detection and recovery.
- [ ] Add events, Redis if justified, and WebSocket updates.
- [ ] Measure throughput and latency.

### Phase 6 — AI operations (optional)

- [ ] Add permissioned mission planning and diagnostic agents.
- [ ] Add local/cloud LLM adapters and human approval paths.
- [ ] Evaluate correctness, safety and reliability.

### Phase 7 — Security and deployment

- [ ] Add authentication and authorization.
- [ ] Add structured audit logging, rate limits and security tests.
- [ ] Add CI/CD, complete Docker applications, staging and production runbooks.

### Phase 8 — Physical robot research

- [ ] Explore ROS 2 / MQTT integrations.
- [ ] Develop hardware adapter interfaces and telemetry contracts.
- [ ] Perform applicable safety engineering before any physical control.

## Documentation

The original numbered documentation organization and both ADRs are retained:

- [Project Overview](docs/01-Project-Overview.md)
- [Requirements](docs/02-REQUIREMENTS.md)
- [Architecture](docs/03-ARCHITECTURE.md)
- [System Design](docs/04-SYSTEM-DESIGN.md)
- [API Design](docs/05-API-DESIGN.md)
- [Database Design](docs/06-DATABASE-DESIGN.md)
- [Robot Simulation](docs/07-ROBOT-SIMULATION.md)
- [Mission Scheduling](docs/08-MISSION-SCHEDULING.md)
- [Safety and Security](docs/09-SAFETY-AND-SECURITY.md)
- [Testing Strategy](docs/10-TESTING-STRATEGY.md)
- [Deployment Design](docs/11-DEPLOYMENT.md)
- [Development Roadmap](docs/12-DEVELOPMENT-ROADMAP.md)
- [ADR 0001 — Technology Stack](docs/ADR/0001-TECHNOLOGY-STACK.md)
- [ADR 0002 — Local Development Infrastructure](docs/ADR/0002-LOCAL-DEVELOPMENT-INFRASTRUCTURE.md)

**Documentation maintenance:** Some previously uploaded numbered designs reflect the **original planned architecture** (Next.js, simulator telemetry, WebSockets, early robot count). They should be interpreted as historical/proposed where they conflict with the current source. This README documents the current demonstration and explicitly separates subsequent plans; update the numbered documents consistently before claiming the entire documentation set is synchronized.

## Contributing

Contributions, bug reports, technical feedback and architectural discussion are welcome. Read [CONTRIBUTING.md](CONTRIBUTING.md) for setup, coding standards, branches and pull-request guidance. Contributions must not bypass safety or state-validity checks.

## Safety disclaimer

FleetOS is a **simulation and software research platform**. It is not certified for safety-critical use or intended to operate physical robots without additional engineering. Simulated routes and animation do **not** demonstrate safe navigation, localization accuracy, obstacle avoidance, protective stopping or regulatory compliance. Physical deployment requires risk assessment, hardware safeguards, testing and validation against the applicable robotics and machinery requirements. AI agents, if added, may advise but must never override deterministic operational or robot-local safety mechanisms.

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE).
