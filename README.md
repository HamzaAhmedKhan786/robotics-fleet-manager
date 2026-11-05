
# Robotics Fleet Manager

An open-source robotics fleet management platform for autonomous mobile robots (AMRs), designed for mission orchestration, real-time monitoring, intelligent task scheduling, robot simulation, and scalable fleet coordination.

> **Project Status:** Early development. The Pixi environment and FastAPI starter are operational. PostgreSQL 18 connectivity has been verified locally. Database models, Redis integration, robot simulation, scheduling, and frontend features are planned unless explicitly marked as implemented.

## Overview

Robotics Fleet Manager is a software engineering project exploring how autonomous mobile robots can be coordinated in warehouses, logistics centers, and industrial facilities.

The goal is to develop a reliable fleet orchestration platform capable of:

- Assigning and managing robot missions.
- Monitoring robot health, position, battery, and connectivity.
- Coordinating shared warehouse resources.
- Scheduling tasks according to operational constraints.
- Detecting failures and recovering interrupted operations.
- Simulating robot behavior before physical deployment.

The initial implementation focuses on simulated autonomous mobile robots.

Physical robot integration and ROS 2 support are future objectives.

## Project Classification

- Robotics and Autonomous Systems
- Distributed Systems
- Fleet Orchestration
- Real-Time Monitoring
- Operations Research and Scheduling
- Digital Twin and Simulation
- Optional Agentic AI and Multi-Agent Systems

## Planned Capabilities

| Capability | Description |
|---|---|
| Robot registry | Register and manage robots and their capabilities |
| Fleet monitoring | Monitor robot position, battery, connectivity, and status |
| Mission management | Create, assign, execute, cancel, and track missions |
| Task scheduling | Assign missions based on availability and operational constraints |
| Robot simulation | Simulate robot movement, battery consumption, and failures |
| Traffic coordination | Manage shared routes and restricted warehouse zones |
| Event streaming | Publish fleet updates to the dashboard |
| Operational recovery | Detect offline robots and recover interrupted missions |
| Observability | Monitor application health, performance, and fleet events |
| Security | Authenticate operators and authorize sensitive operations |

These capabilities describe the intended system and are not yet fully implemented.

## Technology Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js, React, TypeScript, Tailwind CSS |
| Backend | Python 3.12, FastAPI, Pydantic |
| Python environment | Pixi |
| Database | PostgreSQL, SQLAlchemy, Alembic |
| PostgreSQL driver | asyncpg |
| Cache and coordination | Redis |
| Real-time dashboard | WebSockets |
| Robot simulation | Python |
| Robot integration (future) | ROS 2, MQTT |
| Containerization | Docker Compose |
| Testing | Pytest, Playwright |
| CI/CD | GitHub Actions |

The technology stack will be implemented incrementally.

## High-Level Architecture

```mermaid
flowchart TD
    UI["Next.js Fleet Dashboard"]
    API["FastAPI Backend"]
    CORE["Fleet Orchestration Core"]
    SCHED["Mission Scheduler"]
    STATE["Robot State Manager"]
    TRAFFIC["Traffic Coordinator"]
    DB[("PostgreSQL")]
    REDIS[("Redis")]
    SIM["Robot Simulator"]
    ROS["ROS 2 Adapter - Future"]

    UI <-->|REST / WebSocket| API
    API --> CORE
    CORE --> SCHED
    CORE --> STATE
    CORE --> TRAFFIC
    CORE --> DB
    CORE --> REDIS
    CORE <--> SIM
    CORE -.-> ROS
```

This diagram represents the planned logical architecture, not a fully deployed system.

### Architectural Responsibilities

**FastAPI Backend**

Provides REST APIs, request validation, and future WebSocket communication.

**Fleet Orchestration Core**

Coordinates robot management, mission execution, and operational state.

**Mission Scheduler**

Assigns missions according to robot availability, capabilities, battery levels, and operational constraints.

**Robot State Manager**

Maintains robot status, telemetry, and operational state transitions.

**Traffic Coordinator**

Will manage shared resources, restricted areas, and potential route conflicts.

**PostgreSQL**

Stores persistent records, including robots, missions, assignments, and operational events.

**Redis**

Will support temporary state, caching, and event distribution where appropriate. PostgreSQL remains the authoritative store for persistent mission state.

**Robot Simulator**

Will simulate robot movement, mission execution, battery consumption, connectivity problems, and failures.

## Repository Structure (Planned)

The following structure represents the intended repository layout. Some directories and services will be created in later development phases.

```text
robotics-fleet-manager/
├── apps/
│   ├── frontend/
│   └── backend/
│       ├── main.py
│       ├── api/
│       ├── core/
│       ├── db/
│       ├── models/
│       ├── schemas/
│       └── services/
├── services/
│   └── robot-simulator/
├── packages/
│   └── shared-schemas/
├── infrastructure/
│   └── docker/
├── docs/
│   └── ADR/
├── tests/
├── pixi.toml
├── pixi.lock
├── requirements.txt
├── compose.yaml
├── .env.example
├── .gitignore
├── .gitattributes
├── CONTRIBUTING.md
├── LICENSE
└── README.md
```

## Getting Started

### Prerequisites

For the Windows hybrid development environment:

- Git
- Pixi
- PostgreSQL 18
- Windows 11
- Docker Desktop (for Redis when required)
- Node.js LTS (for the planned frontend)

Python 3.12 is managed through Pixi, so a separate system-wide Python installation is not required.

A full Docker-based infrastructure setup may be used on other supported development environments.

### 1. Clone the Repository

```powershell
git clone https://github.com/HamzaAhmedKhan786/robotics-fleet-manager.git
cd robotics-fleet-manager
```

### 2. Install Python Dependencies

Pixi manages the Python runtime and project dependencies.

```powershell
pixi install
```

Verify Python:

```powershell
pixi run python --version
```

Expected Python version: 3.12.x.

### 3. Configure Environment Variables

Create your local environment file if it does not already exist:

```powershell
Copy-Item .env.example .env
```

Do not overwrite an existing configured `.env`.

Example configuration:

```dotenv
# Application
APP_NAME=Robotics Fleet Manager
APP_ENV=development
LOG_LEVEL=INFO

# PostgreSQL
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=robotics_fleet
POSTGRES_USER=postgres
POSTGRES_PASSWORD=CHANGE_ME

DATABASE_URL=postgresql+asyncpg://postgres:CHANGE_ME@localhost:5432/robotics_fleet

# Redis
REDIS_URL=redis://localhost:6379/0

# JWT authentication (planned)
JWT_SECRET=GENERATE_A_UNIQUE_RANDOM_SECRET
JWT_ALGORITHM=HS256

# Simulation (planned)
SIMULATION_ENABLED=true
SIMULATION_ROBOT_COUNT=5
SIMULATION_TICK_SECONDS=1
```

Replace placeholders with your own local credentials.

If a password contains reserved URL characters, its representation inside `DATABASE_URL` must be properly URL-encoded.

Generate a secure JWT secret:

```powershell
pixi run python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Authentication implementation is planned; configuring these values does not yet enable JWT authentication.

Never commit `.env`, passwords, JWT secrets, or production credentials to Git.

### 4. Development Infrastructure

The primary development environment uses a hybrid setup to reduce resource consumption on Windows machines with limited RAM.

| Component | Execution Environment | Address |
|---|---|---|
| FastAPI backend | Windows / Pixi | `127.0.0.1:8000` |
| PostgreSQL 18 | Native Windows service | `localhost:5432` |
| Redis | Docker container (planned) | `localhost:6379` |
| Robot simulator | Windows / Pixi (planned) | Python process |
| Frontend | Windows / Node.js (planned) | Development server |

This changes the local deployment topology without changing the intended logical application architecture.

#### 4.1 PostgreSQL Setup

PostgreSQL runs as an existing native Windows service.

Check the PostgreSQL service:

```powershell
Get-Service *postgres*
```

Verify that port 5432 is listening:

```powershell
Get-NetTCPConnection -LocalPort 5432 -State Listen -ErrorAction SilentlyContinue
```

Connect using the PostgreSQL 18 command-line client:

```powershell
& "C:\Program Files\PostgreSQL\18\bin\psql.exe" -U postgres -h localhost -p 5432 -d postgres
```

Create the project database if it does not exist:

```sql
CREATE DATABASE robotics_fleet;
```

Verify the database list:

```text
\l
```

Exit PostgreSQL:

```text
\q
```

The `robotics_fleet` database has been created and direct connectivity from Python using `asyncpg` has been verified in the primary local development environment.

For initial local setup, the existing PostgreSQL administrator account may be used. A dedicated application user with restricted permissions is recommended for subsequent development and production.

SQLAlchemy integration and Alembic migrations are upcoming implementation steps.

#### 4.2 Redis Setup — Docker (Planned)

Redis will run in a dedicated Docker container rather than installing another native database service.

Start only Redis:

```powershell
docker compose up -d redis
```

Verify the Redis service:

```powershell
docker compose ps
docker compose exec redis redis-cli ping
```

Expected response:

```text
PONG
```

Stop Redis when it is no longer needed:

```powershell
docker compose stop redis
```

Redis container startup and application integration have not yet been verified.

**Important:** For the Windows hybrid setup, avoid running:

```powershell
docker compose up -d
```

without specifying a service.

The existing `compose.yaml` also defines PostgreSQL. Starting the full stack may conflict with the native PostgreSQL service on port 5432 and consume unnecessary resources.

Docker Desktop itself may introduce additional WSL2 memory overhead. Resource usage should be monitored during Redis testing.

#### 4.3 Full Docker Infrastructure — Alternative

The repository retains Docker Compose definitions for PostgreSQL and Redis.

On machines where native PostgreSQL is not already running, developers may use the full Compose infrastructure after configuring `.env` and ensuring the required ports are available.

The hybrid Windows configuration is a development convenience, not a requirement for production deployment.

### 5. Start FastAPI Backend

The initial FastAPI backend is implemented.

Start the development server:

```powershell
pixi run backend
```

The application is available at:

- API documentation: http://127.0.0.1:8000/docs
- Health endpoint: http://127.0.0.1:8000/health
- Fleet summary: http://127.0.0.1:8000/api/v1/fleet/summary

Example health response:

```json
{
  "status": "healthy",
  "service": "robotics-fleet-manager"
}
```

Example fleet summary response:

```json
{
  "total_robots": 0,
  "active_robots": 0,
  "active_missions": 0
}
```

The fleet summary currently returns placeholder values.

The health endpoint verifies application responsiveness but does not yet verify PostgreSQL or Redis connectivity.

### 6. Start Frontend (Planned)

After the Next.js frontend has been initialized:

```powershell
cd apps/frontend
npm install
npm run dev
```

The frontend will provide fleet visualization, robot monitoring, mission management, and operational dashboards.

These features are not yet implemented.

## Implementation Status

| Component | Status | Notes |
|---|---|---|
| Git repository | Completed | Initial source and documentation |
| Pixi environment | Completed | Python 3.12 environment working |
| FastAPI starter | Completed | Basic API routes operational |
| PostgreSQL 18 installation | Available | Existing local Windows service |
| Project database | Completed locally | `robotics_fleet` created |
| PostgreSQL connectivity | Verified locally | Direct `asyncpg` connection |
| SQLAlchemy integration | Planned | Database engine, sessions, models |
| Alembic migrations | Planned | Version-controlled schema changes |
| Redis container | Planned | Docker-based local service |
| Redis application integration | Planned | Caching and event distribution |
| Robot registry | Planned | Persistent robot records |
| Mission management | Planned | Mission lifecycle |
| Deterministic scheduling | Planned | Robot assignment rules |
| Robot simulator | Planned | Simulated warehouse robots |
| WebSocket updates | Planned | Real-time fleet events |
| Next.js frontend | Planned | Fleet dashboard |
| Authentication and authorization | Planned | JWT and access controls |
| CI/CD | Planned | Automated validation |
| Production deployment | Not implemented | Future phase |
| ROS 2 integration | Future | Physical robotics integration |

## Development Roadmap

### Phase 1 — Project Foundation

- [x] Create Git repository.
- [x] Define requirements and architecture.
- [x] Configure Pixi.
- [x] Initialize FastAPI.
- [x] Create PostgreSQL database locally.
- [x] Verify PostgreSQL connectivity.
- [ ] Configure and verify Redis container.

### Phase 2 — Persistence Layer

- [ ] Configure SQLAlchemy asynchronous engine.
- [ ] Implement database session management.
- [ ] Define initial database models.
- [ ] Configure Alembic.
- [ ] Create and execute initial migrations.
- [ ] Add database integration tests.

### Phase 3 — Fleet Management

- [ ] Implement robot registration.
- [ ] Implement robot status management.
- [ ] Add robot capability definitions.
- [ ] Persist robot records.
- [ ] Implement fleet monitoring APIs.

### Phase 4 — Mission Orchestration

- [ ] Define mission lifecycle.
- [ ] Implement mission creation and cancellation.
- [ ] Implement deterministic mission scheduling.
- [ ] Handle assignment conflicts.
- [ ] Add mission event history.

### Phase 5 — Robot Simulation

- [ ] Simulate multiple robots.
- [ ] Simulate movement and battery consumption.
- [ ] Simulate mission execution.
- [ ] Simulate connectivity failures.
- [ ] Test fleet recovery behavior.

### Phase 6 — Real-Time Monitoring

- [ ] Implement WebSocket communication.
- [ ] Integrate Redis where required.
- [ ] Publish robot telemetry and mission events.
- [ ] Build Next.js fleet dashboard.

### Phase 7 — Reliability and Security

- [ ] Implement authentication and authorization.
- [ ] Add structured logging.
- [ ] Add operational metrics.
- [ ] Implement resilience and recovery tests.
- [ ] Validate concurrent scheduling behavior.

### Phase 8 — Deployment

- [ ] Add automated CI checks.
- [ ] Build application containers.
- [ ] Configure staging deployment.
- [ ] Add monitoring and backups.
- [ ] Prepare production deployment documentation.

### Future Research

- ROS 2 integration.
- Hardware robot adapters.
- Multi-robot traffic optimization.
- Advanced path planning.
- AI-assisted scheduling.
- Digital twin enhancements.

## Documentation

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
- [Technology Stack ADR](docs/ADR/0001-TECHNOLOGY-STACK.md)

The local hybrid infrastructure decision is documented in `docs/ADR/0002-LOCAL-DEVELOPMENT-INFRASTRUCTURE.md` when that file is added to the repository.

## Contributing

Contributions, bug reports, architectural discussions, and improvement proposals are welcome.

Please review [CONTRIBUTING.md](CONTRIBUTING.md) before submitting a pull request.

## Safety Disclaimer

This project is initially a simulation and research platform.

It is not certified for safety-critical control of physical robots.

Physical deployment requires additional validation, risk assessment, safety engineering, hardware-specific safeguards, and compliance with applicable robotics and machinery safety requirements.

## License

This project is licensed under the MIT License.

See [LICENSE](LICENSE) for details.
