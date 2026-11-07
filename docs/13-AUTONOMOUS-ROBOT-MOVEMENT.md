# FleetOS — Autonomous Robot Movement Engine

**Status:** Implemented and validated in the local development environment. Rust unit-test execution remains blocked by Windows Application Control; independent execution is required before merging.

## 1. Overview

The FleetOS Autonomous Robot Movement Engine provides backend-authoritative movement simulation for autonomous mobile robots (AMRs) operating inside a warehouse.

It integrates **Rust, Python, PostgreSQL, FastAPI, and React Three.js** to calculate robot routes, simulate movement, persist positions, and visualize robot operations in a 3D digital twin.

The backend is the authoritative source of simulated robot positions. The frontend renders and smooths movement between persisted position updates.

## 2. Core Components

### 2.1 Rust Movement Engine

The Rust implementation provides three main capabilities:

- **`shortest_path`** — Deterministic Dijkstra shortest-path routing using directed, weighted graph edges.
- **`sample_route`** — Smooth interpolation of warehouse display coordinates based on elapsed mission time.
- **`estimate_energy`** — Deterministic linear battery-consumption estimation.

Energy estimates are simulation assumptions and are not calibrated against physical robot hardware.

### 2.2 Python Autonomous Simulation Worker

The Python worker manages simulated movement throughout the mission lifecycle.

It:

- Uses `mission.started_at` and `plan.duration_seconds` to determine mission progress.
- Calls the Rust movement engine to obtain simulated positions.
- Saves robot X/Z coordinates and progress in PostgreSQL at each simulation tick.
- Completes missions when the required simulated duration has elapsed.
- Updates the robot's final position to the exact delivery-station coordinates.

Battery consumption is applied once by the existing mission-completion service.

### 2.3 PostgreSQL Position Persistence

PostgreSQL stores the authoritative simulated state using the following robot fields:

| Field | Purpose |
|---|---|
| `position_x` | Current simulated X coordinate |
| `position_z` | Current simulated Z coordinate |
| `movement_progress` | Current mission movement progress |
| `position_updated_at` | Timestamp of the latest simulated position update |

The corresponding Alembic migration is:

`e20261107a001_add_robot_simulated_position.py`

### 2.4 FastAPI Integration

The existing robot-management API exposes the persisted robot-position information through its response schemas.

This allows frontend applications to retrieve simulated telemetry without independently calculating the mission's elapsed-time progress.

### 2.5 React Three.js Digital Twin

The FleetOS 3D warehouse visualizes backend-authoritative robot movement.

Key capabilities include:

- Displaying simulated AMR positions.
- Smoothing visual movement between backend snapshots.
- Showing mission routes and robot status.
- Selecting individual robots.
- Displaying position, battery, mission progress, and operating state through `RobotDetailsPanel.tsx`.

React does not independently calculate route progress using the browser's wall clock.

## 3. Movement Lifecycle

1. An operator creates a warehouse mission.
2. The scheduler selects an eligible robot.
3. The mission is assigned and started.
4. The Python worker calculates elapsed mission time.
5. Rust calculates the corresponding simulated position.
6. PostgreSQL stores the updated coordinates and progress.
7. FastAPI exposes the latest persisted robot state.
8. React animates the 3D robot toward the latest authoritative position.
9. The mission completes at the delivery station.
10. The mission-completion service applies battery consumption and releases the robot when eligible.

## 4. Technical Limitations

This system is a **warehouse movement simulation**, not physical robot navigation or localization.

The current implementation does not provide:

- Multi-robot collision avoidance or shared-aisle reservations.
- Physical velocity and acceleration constraints.
- Safety-rated robotics behavior.
- Recovery after corrupted simulation state.
- Operator authentication and authorization.
- Distributed, multi-process worker coordination.

### Simulation Worker Constraint

The current autonomous dispatcher runs through the FastAPI application lifespan.

Only one backend worker process should run in this local demonstration environment.

Do not start `scripts.auto_worker` separately while the FastAPI lifespan worker is active.

### Telemetry Update Frequency

The simulation uses approximately:

- **1-second backend simulation ticks**
- **2-second frontend polling**

This may produce discontinuous telemetry updates. React uses visual interpolation to smooth movement between persisted snapshots.

### Warehouse Coordinate Consistency

Current route-planning weights and 3D display coordinates are not fully aligned.

| Warehouse dimension | Route graph | 3D visualization |
|---|---|---|
| Horizontal connection | 10 units | 6 units |
| Vertical connection | 8 units | 8 units |

Shortest-path planning uses graph weights, while visual interpolation uses warehouse display coordinates.

A future development milestone should unify the warehouse coordinate system and movement-distance metrics.

## 5. Installation and Database Migration

The implementation is integrated into the existing FleetOS project.

The original installation package contains `INSTALL-OPTION-B.md`; that is a legacy installation-guide filename and does not affect runtime behavior.

Database migrations are managed through Alembic:

```powershell
pixi run alembic upgrade head
pixi run alembic current
```

The development and test databases must both contain the required position fields.

## 6. Verification and Testing

### Rust

```powershell
cd crates/fleet-scheduler
cargo build
cargo test --no-run
cargo test
cd ../..
```

Rust compilation and test compilation have passed locally. Actual Rust unit-test execution was blocked by Windows Application Control and remains an outstanding verification item.

### Python

```powershell
pixi run pytest tests -q --tb=short
pixi run ruff check apps tests scripts alembic
pixi run pyright apps/backend
```

**Local verification results:**

- 43 Python tests passed.
- Ruff checks passed.
- Pyright reported zero errors and warnings.

### React

```powershell
cd frontend
npm run build
cd ..
```

The React production build passed.

### End-to-End Simulation

The local simulation was manually verified with a registered AMR executing a mission from `STATION-A2` to `STATION-B3`, starting at `STATION-A1`.

The observed simulation included robot movement, position updates, mission progress, and successful mission completion.

## 7. Future Development Milestones

The following features are **planned and not yet implemented**:

1. Unified warehouse coordinate and routing metrics.
2. Per-segment movement metrics and speed constraints.
3. Multi-robot route-conflict detection and collision avoidance.
4. Shared-aisle reservations and traffic coordination.
5. Acceleration and deceleration modeling.
6. Mission checkpointing, pausing, and restarting.
7. Simulation-state validation and failure recovery.
8. Historical robot-position events and movement replay.
9. WebSocket-based real-time telemetry streaming.
10. Distributed worker coordination and lifecycle management.
11. Operator authentication, authorization, and operational auditing.
12. ROS 2 integration and physical robot communication.

## 8. Conclusion

The FleetOS Autonomous Robot Movement Engine establishes backend-authoritative movement simulation across Rust, Python, PostgreSQL, FastAPI, and React Three.js.

The implemented system supports deterministic movement calculations, persisted simulated coordinates, automated mission execution, and interactive 3D visualization.

The next major engineering milestone is **Multi-Robot Traffic Coordination and Collision Avoidance**, followed by fault recovery and more realistic simulation dynamics.