# FleetOS — Advanced Autonomous Fleet Operations

## Status and scope

This package delivers a **single milestone integration candidate**, NOT a verified production robotics release. It contains coordinate-unified routing primitives, velocity-profile simulation, traffic arbitration, resumable progress metadata, persisted snapshots, database audit history, polling-backed WebSocket telemetry, a PostgreSQL advisory scheduler lock, local JWT operator controls, a React telemetry panel, a read-only ROS 2 adapter, and GitHub Actions.

## Safety and deployment limits

- **Not safety rated.** No physical robot actuation, collision certification, emergency-stop device integration, or real localization is provided.
- Traffic arbitration checks proposed position segments against other robots' last persisted positions and accepted moves; it is a conservative discrete simulator, not continuous-time multi-agent planning. Deadlock avoidance is not mathematically proven.
- Worker-lock scope is a single PostgreSQL database. All workers must use the same database and tick function.
- Local authentication uses JWTs, password hashing and viewer/operator/admin roles, with optional enforcement for existing API endpoints. Missing production controls include MFA, federation, rate limits, token revocation, mandatory TLS and comprehensive audit coverage.
- WebSocket telemetry sends PostgreSQL snapshots once a second, not an event-broker stream; production needs bounded backpressure and stream authorization.
- History table may grow without bound; apply retention/partitioning before load tests.
- ROS 2 adapter is a read-only publisher to `/fleetos/simulated_fleet`, not a robot-control gateway. Run only in a separate ROS 2 environment.
- Checkpoints are persisted in JSONB mission plans and continue across worker restarts. Pauses are made via operator API only.
- Existing mission durations are replaced by profile-based elapsed simulation time for newly active missions. Current in-progress missions should be allowed to finish before migration.

## One-milestone workstreams and acceptance status

1. **Rust unit tests:** Linux GitHub Actions job provided; needs a successful run on the merged checkout.
2. **Metric unification:** Warehouse graph generated from one server-side station layout (6 horizontal, 8 vertical simulation metres); coordinates are included in the warehouse API and consumed by React.
3. **Per-segment speed:** Python per-segment acceleration-limited profiles included, stopping at junctions; Rust remains responsible for the existing path planning and energy components. Port profile sampling to Rust for full Rust motion-engine parity.
4. **Collision detection:** Discrete conflict arbitration code provided; unit tests include crossing segments and 15 independent robots, but live 15-robot congestion and adversarial deadlock tests still required.
5. **Shared-aisle traffic:** Short-duration reservations persisted to PostgreSQL and cross-checked at each simulation tick. This is not full advance time-window scheduling.
6. **Acceleration:** Trapezoidal/triangular velocity profiles provided.
7. **Pause/resume/restart:** Authenticated development API and JSON checkpoints; endpoint and worker concurrency tests required.
8. **Recovery:** Persisted checkpoint time and transactional snapshots; fault injection needed.
9. **History:** SQL migration + robot event records + history API and React replay scrubber.
10. **WebSocket:** Authenticated development telemetry channel and React subscriber.
11. **Distributed coordination:** PostgreSQL advisory transaction lock keeps one scheduler tick active per database, with a persisted leader heartbeat.
12. **Authentication:** Database-backed local accounts, JWT, viewer/operator/admin route restrictions when enabled. Production identity controls remain outstanding.
13. **ROS 2:** Read-only telemetry publishing bridge included; no physical-robot command pipeline or hardware acceptance tests.

## Installing

1. Back up your database and commit or stash local changes.
2. Switch from `main` to `feat/advanced-autonomous-fleet`.
3. Extract archive outside repo, run `pixi run python <package>/apply_milestone.py --dry-run` then run without `--dry-run` from repository root.
4. Bootstrap an admin with `pixi run python -m scripts.bootstrap_admin`, sign in via `/api/v1/auth/login`, and enable `FLEETOS_REQUIRE_AUTH=1` in the server environment. Never put the JWT secret in Vite variables.
5. Apply `pixi run alembic upgrade head` to dev DB and separately to `robotics_fleet_test`.
6. Run full checks in `VALIDATE.ps1` and review the changes.
7. Push feature branch and use CI to verify Rust tests.

## Evidence needed before accepting full completion

Traffic tests with 15 robots, blocked-aisle deadlock scenarios, concurrent workers, failure injection, audit review, real identity-provider authorization, and a ROS 2 simulator integration run. Do **not** claim those are completed by this package.
