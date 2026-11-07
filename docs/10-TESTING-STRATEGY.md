# Testing Strategy — FleetOS

## 1. Purpose

Verify scheduling invariants, API data consistency, simulated movement, frontend build quality and operational failure handling. Separate tests that have actually passed from tests merely proposed. A prior local run reported **39 passing Pytest tests**, which is not a benchmark and not proof of the full Option B design.

## 2. Current validation commands

From repository root:

```powershell
pixi run ruff check apps tests scripts alembic
pixi run pyright apps/backend
pixi run pytest tests -q --tb=short
```

From `frontend`:

```powershell
npm run build
```

Build compiles TypeScript and bundles Vite; it does not test camera behavior or movement correctness. Cargo tests should be added/expanded when Rust route and motion modules grow:

```powershell
cargo test --manifest-path crates/fleet-scheduler/Cargo.toml
```

## 3. Test database isolation

Integration test fixture uses `robotics_fleet_test`. Apply Alembic migrations **separately** to development and test databases. The test fixture may delete test robot/mission rows; never direct it at `robotics_fleet` or a production database.

```powershell
$env:POSTGRES_DB = 'robotics_fleet_test'
pixi run alembic upgrade head
Remove-Item Env:POSTGRES_DB
```

## 4. Scheduler unit tests

- Candidate ranking: shortest pickup distance, battery tie, deterministic identifier tie.
- Invalid station and unreachable graph connections.
- Energy reserve boundary and exact minimum battery.
- Priority ordering and stable queue processing.
- No assignment to unavailable/busy robots.
- Explanations match actual selection inputs.

## 5. Integration and concurrency tests

- Robot creation and state validation.
- Mission creation and automatic assignment.
- Database transaction conflicts between competing schedulers.
- All eligible robots busy: remain pending, then dispatch on release.
- Repeated demo calls: create missions, **zero new robots**.
- Manual registration capacity: 15 allowed, 16th rejected, including simultaneous registration attempts.
- Cancel and complete sequences are valid and idempotent.

## 6. Option B movement tests (future)

Rust `advance()` tests with deterministic fixed dt, zero and large time steps, start/finish boundaries, no teleporting, direction/orientation, straight and multi-edge routes, pause/restart and remaining energy. Integration tests assert committed x/z, segment and progress persist across browser reload and worker restart. UI interpolation must never trigger mission completion.

## 7. Frontend/E2E tests (future)

With Playwright: open overview, switch 2D/3D, create robot and mission, inspect queue, watch route changes, verify completed status and search. Visual regression screenshots should be stable and use deterministic simulated time where possible.

## 8. Security/reliability and CI (future)

Ruff/Pyright/Pytest/Cargo/TypeScript build as PR checks; then auth, cross-origin, invalid inputs, worker failure, database outage and restart tests. Measure API latency and simulation throughput before making performance claims.

## 9. Reporting

Document the exact commit, test database revision, command, date, counts and any skipped tests. Do not claim Rust benchmarking or production E2E success until results exist.

---

## Original specification retained for traceability (historical baseline)

> **Historical reference, not a statement of current implementation.** The original text below is preserved so that no early requirement, design option, setup explanation, or proposed feature is lost. Where it differs from the current sections above, **the current sections take precedence**. In particular, references to Next.js, 20 robots, WebSocket telemetry, continuous movement, Redis integration, A* navigation, authentication, or physical control may describe earlier proposals rather than implemented behavior. Review original setup commands against the current repository before running them.

# Testing Strategy

## 1. Objectives

Validate business logic, mission consistency, simulation behavior, security, and failure recovery.

## 2. Unit Tests

Test:
- Robot eligibility
- Mission state transitions
- Battery calculations
- Scheduling scores
- Pathfinding
- Command validation

Framework: Pytest

## 3. Integration Tests

Test:
- FastAPI and PostgreSQL
- Database migrations
- Scheduler transactions
- Redis integration
- Simulator communication

## 4. API Tests

Test:
- Successful requests
- Invalid input
- Unauthorized access
- Missing resources
- Conflicting mission assignments
- Idempotent operations

## 5. End-to-End Tests

Framework: Playwright

Scenarios:
1. Open dashboard.
2. Register a simulated robot.
3. Create a mission.
4. Observe assignment.
5. Monitor movement.
6. Verify completion.
7. Inspect mission history.

## 6. Failure Tests

- Robot disconnect
- Delayed telemetry
- Duplicate messages
- Database interruption
- Scheduler restart
- Mission cancellation
- Insufficient battery
- Blocked route

## 7. Performance Tests

Initial targets:
- 20 simulated robots
- One telemetry update per robot per second
- Five concurrent missions

Measure:
- API latency
- Scheduler processing time
- WebSocket delivery delay
- Database query performance
- CPU and memory utilization

## 8. CI Pipeline

Planned GitHub Actions checks:
- Ruff linting
- Pyright type checking
- Pytest
- Frontend ESLint
- TypeScript checking
- Playwright tests
- Dependency vulnerability checks

No test results should be reported until the tests have actually run.
