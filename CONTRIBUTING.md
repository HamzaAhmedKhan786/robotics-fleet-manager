
# Contributing to FleetOS

Thank you for your interest in contributing to Robotics
Fleet Manager (FleetOS).

FleetOS is an open-source, simulation-first robotics fleet
management platform for autonomous mobile robots (AMRs).

The project currently includes a functional local prototype
with Python, FastAPI, PostgreSQL, Rust, React, and a 3D
warehouse visualization.

Contributions, bug reports, design proposals, documentation
improvements, and technical discussions are welcome.

## 1. Project Architecture

FleetOS uses the following technologies:

| Component | Technology |
|---|---|
| Frontend | React, TypeScript, Vite |
| 3D visualization | Three.js, React Three Fiber, Drei |
| Backend | Python 3.12, FastAPI |
| Database | PostgreSQL, SQLAlchemy, Alembic |
| Scheduling | Rust, PyO3, Maturin |
| Simulation orchestration | Python asyncio |
| Environment management | Pixi |
| Testing | Pytest, Ruff, Pyright, Cargo, TypeScript |

### Architectural responsibilities

- Python manages API requests, persistence, mission
  orchestration, and worker execution.
- Rust currently provides deterministic robot selection.
- PostgreSQL stores authoritative robot and mission records.
- React provides fleet-management interfaces.
- Three.js visualizes the simulated warehouse and robots.

Future development will expand Rust to cover routing,
energy calculations, and movement simulation.

## 2. Development Prerequisites

Install the following:

- Git
- Pixi
- Node.js and npm
- Rust and Cargo
- PostgreSQL
- Python dependencies managed through Pixi

Docker Desktop is optional for local Redis or alternative
PostgreSQL infrastructure.

The primary development environment uses Windows and
native PostgreSQL 18.

## 3. Repository Setup

Clone the repository:

```powershell
git clone https://github.com/HamzaAhmedKhan786/robotics-fleet-manager.git

cd robotics-fleet-manager
```

Install Python dependencies:

```powershell
pixi install
```

Check your Python version:

```powershell
pixi run python --version
```

Install frontend dependencies:

```powershell
cd frontend
npm ci
cd ..
```

Verify Rust:

```powershell
rustc --version
cargo --version
```

### Database configuration

Create a local `.env` file containing your database
configuration.

Do not commit `.env` or database credentials.

Create the local development database and apply migrations
using the project's Alembic configuration.

```powershell
pixi run alembic upgrade head
```

Run this only after confirming that DATABASE_URL points to
the intended development database.

## 4. Running FleetOS

### Backend

From the project root:

```powershell
pixi run backend
```

Backend:

http://127.0.0.1:8000

API documentation:

http://127.0.0.1:8000/docs

### Frontend

Open a separate terminal:

```powershell
cd frontend
npm run dev
```

Frontend:

http://127.0.0.1:5173/overview

### Autonomous mission worker

The autonomous dispatcher must run exactly once.

If it is already started by the FastAPI application
lifespan, do not launch another instance.

For configurations using the standalone worker:

```powershell
pixi run python -m scripts.auto_worker
```

Check the current application startup configuration before
choosing the standalone-worker option.

## 5. Branch Naming

Use meaningful branch names:

- feat/feature-name
- fix/issue-name
- docs/documentation-update
- test/test-description
- refactor/component-name
- perf/optimization-name

Create a feature branch before making changes.

Example:

```powershell
git checkout -b feat/rust-movement-engine
```

## 6. Coding Standards

### Python

- Use type hints.
- Follow Ruff linting and formatting requirements.
- Use Pydantic for API validation.
- Use SQLAlchemy for database persistence.
- Keep business logic separate from HTTP handlers.
- Prefer async interfaces where appropriate.
- Add automated tests for changed behavior.
- Preserve valid mission-state transitions.
- Handle database transactions correctly.

### Rust

- Use Rust formatting conventions.
- Keep simulation calculations deterministic.
- Avoid unnecessary allocations in hot paths.
- Validate inputs at Python/Rust boundaries.
- Use explicit errors rather than unchecked panics.
- Add unit tests for scheduling and movement logic.
- Maintain compatibility with the PyO3 interface.
- Update Python type stubs when exported APIs change.

### TypeScript and React

- Use strict TypeScript.
- Prefer reusable React components.
- Maintain clear API response types.
- Handle loading, errors, and empty states.
- Avoid unnecessary network requests.
- Keep 3D rendering separate from business logic.
- Do not treat browser animation as authoritative telemetry.
- Ensure responsive dashboard behavior.

### Database

- Define schema changes through Alembic migrations.
- Do not manually modify production schemas.
- Provide upgrade paths for schema changes.
- Preserve data integrity and foreign key constraints.
- Consider concurrent mission assignments.
- Add integration tests when persistence behavior changes.

## 7. FleetOS Engineering Rules

### Robot registration

The agreed local prototype policy is:

- Maximum 15 registered robots.
- Robots are registered manually.
- Demo generation must not create robots automatically.
- Robot registration limits must be enforced by the backend.

### Mission assignment

- Missions may only be assigned to eligible robots.
- A robot must not receive conflicting active assignments.
- Battery feasibility must be checked.
- Pending missions must remain queued when no eligible
  robot is available.
- Mission scheduling must be deterministic and testable.

### Simulation

- Keep simulated and physical robot operations separate.
- Never represent estimated browser positions as live
  hardware telemetry.
- Preserve validated mission lifecycle rules.
- Avoid introducing hidden automatic robot provisioning.

### Future AI integration

AI agents may recommend missions or assist operators,
but they must not bypass deterministic validation,
authorization, or robotics safety constraints.

## 8. Testing

Run checks from the project root unless stated otherwise.

### Python linting

```powershell
pixi run ruff check apps tests scripts alembic
```

### Python type checking

```powershell
pixi run pyright apps/backend
```

### Python tests

```powershell
pixi run pytest tests -q --tb=short
```

### Frontend build

```powershell
cd frontend
npm run build
cd ..
```

### Rust formatting

```powershell
cd crates/fleet-scheduler
cargo fmt --check
cd ../..
```

### Rust tests

```powershell
cd crates/fleet-scheduler
cargo test
cd ../..
```

All relevant tests should pass before submitting a
pull request.

If a check cannot run in your environment, explain why
in the pull request.

## 9. Documentation Requirements

When introducing or changing functionality:

1. Update the root README when appropriate.
2. Update relevant documents under docs/.
3. Update API design documents for endpoint changes.
4. Update database design for schema changes.
5. Update architecture diagrams for structural changes.
6. Record major architecture decisions in an ADR.
7. Clearly distinguish implemented and planned features.

Do not remove historical requirements without explaining
why the decision changed.

## 10. Pull Requests

A pull request should include:

- Summary of the change
- Reason for the change
- Related issues, if applicable
- Technical implementation notes
- Tests performed
- Documentation updates
- Known limitations
- Screenshots for significant UI changes

Keep pull requests focused and reviewable.

## 11. Security

Never commit:

- Environment files containing credentials
- Database passwords
- API keys
- JWT secrets
- Private certificates
- Personal access tokens
- Production secrets

Use environment variables or a suitable secret manager.

Do not submit changes that bypass robot-safety rules or
make unsupported claims about physical robot control.

## 12. Reporting Issues

Provide:

- Problem description
- Expected behavior
- Actual behavior
- Reproduction steps
- Environment information
- Relevant logs
- Screenshots, where useful

Remove credentials and sensitive information before
sharing logs.

## 13. Planned Development Areas

The following are not fully implemented:

- Rust-based movement simulation
- Backend-authoritative robot coordinates
- Advanced traffic coordination
- Collision-conflict management
- WebSocket telemetry streaming
- Redis-backed transient coordination
- Authentication and role-based authorization
- Agentic AI operations
- ROS 2 integration
- Physical robot adapters
- Production deployment and monitoring

Contributions to these areas should follow the project's
architecture and development roadmap.

## 14. Robotics Safety Disclaimer

FleetOS is currently a software simulation and research
platform.

It is not certified for safety-critical control of physical
robots.

Real-world deployment requires additional safety engineering,
hardware validation, risk assessment, and compliance with
applicable robotics and machinery regulations.

## 15. License

By contributing, you agree that your contributions will be
distributed under the project's MIT License.

See LICENSE for details.
