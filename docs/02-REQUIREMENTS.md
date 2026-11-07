# Software Requirements Specification — FleetOS

## 1. Purpose and scope

Define observable behaviors and target requirements for a **simulation-only** fleet coordinator. Current = implemented prototype; target = planned and not yet proven. Physical navigation, certified robot safety and LLM control of actuators are out of scope.

## 2. Actors

- **Operator (current interface):** creates missions, inspects fleet and may register/change robot status.
- **Autonomous worker (current):** polls queued missions and executes simulated lifecycle.
- **Rust scheduler extension (current):** ranks feasible candidates.
- **3D digital twin (current):** renders racks, stations, routes, cart models and inferred motion.
- **Authenticated administrator (target):** user/role provisioning and capacity policy.
- **AI operations agent (future):** proposes tasks and explains decisions through validated tools.

## 3. Current functional behavior

| ID | Requirement | State |
|---|---|---|
| FR-001 | Register robots with unique ID, name, battery, station and status | Implemented API/UI |
| FR-002 | Read robot list/status and fleet summary | Implemented |
| FR-003 | Create pickup/delivery missions, priority 1–5 | Implemented |
| FR-004 | Queue pending missions; dispatch automatically when feasible | Implemented local worker |
| FR-005 | Track pending, assigned, in_progress, completed, failed and cancelled | Implemented model; not all failure scenarios validated |
| FR-006 | Check robot-to-pickup and pickup-to-delivery connectivity | Implemented Python planning |
| FR-007 | Require estimated battery after route to meet safety reserve | Implemented simulation estimate |
| FR-008 | Rank by pickup distance, then battery, then ID | Implemented Rust selector |
| FR-009 | Render 2D warehouse and interactive 3D carts/stations/racks | Implemented |
| FR-010 | Create demo missions without registering robots | Revised policy/endpoint |
| FR-011 | Store route plan and scheduler reason | Implemented in mission schema |
| FR-012 | Publish position-based authoritative telemetry | **Target** |
| FR-013 | Enforce manual-only 15-robot cap at every registration path | **Target — verify enforcement** |
| FR-014 | Safe shared-aisle reservation and collision coordination | **Target** |
| FR-015 | Operator authentication and permissions | **Target** |

## 4. Mandatory fleet business rules

1. Only an operator-triggered registration request may create a robot; the demo never creates robots.
2. Fleet target maximum is 15 registered robots, regardless of availability. Backend must reject a 16th robot consistently, including concurrent requests.
3. An unavailable, unlocated, busy, or energy-infeasible robot must not be assigned.
4. Priority orders pending mission consideration; it does not defeat battery/route constraints.
5. If all robots are busy (including when 15 are working), new jobs remain pending until suitable capacity returns.
6. A robot can hold at most one active mission.
7. Full route comprises robot start → pickup → delivery; selection should explain cost/eligibility.

## 5. Movement contract — Option B target

- Backend stores authoritative simulated (x,z) position, route segment, progress and last update timestamp.
- Rust computes deterministic movement from route, elapsed simulation time and speed; Python persists results.
- Frontend can interpolate between received samples but must not invent mission completion.
- Reopening the browser must preserve the mission state and position.
- Restarting the worker must safely resume or reconcile active missions.
- Movement follows graph edges and respects eventual corridor reservations.
- Battery deductions and mission completion occur once, transactionally.

## 6. Non-functional targets

- Repeatable and deterministic behavior in Rust core with unit tests.
- Database transaction safety and idempotent state transitions.
- Dashboard polling currently about every **2 seconds**; streaming is future work.
- Support **up to 15 registered robots** in the local demo (policy), with stored mission history potentially exceeding fleet size.
- Clear failure logs, no secrets in source control, reproducible Pixi and Node dependency installation.
- No measured latency or throughput targets are asserted as achieved.

## 7. Acceptance tests

- Repeated demo clicks add missions but **never increase robot count**.
- At capacity, a manual registration attempt fails consistently.
- When all eligible robots are busy, new missions stay pending, then dispatch after release.
- Tie-breakers and safety-reserve rules hold in unit and integration tests.
- Routes remain connected and follow graph stations.
- 3D can render multiple robots per station and selected routes.
- Option B: positions remain consistent after refresh and worker restart, with controlled timestamps.

## 8. Out of scope

Physical navigation, emergency stopping, localization quality, safety certification, real perception sensors and unconditional LLM-directed motion commands.

---

## Original specification retained for traceability (historical baseline)

> **Historical reference, not a statement of current implementation.** The original text below is preserved so that no early requirement, design option, setup explanation, or proposed feature is lost. Where it differs from the current sections above, **the current sections take precedence**. In particular, references to Next.js, 20 robots, WebSocket telemetry, continuous movement, Redis integration, A* navigation, authentication, or physical control may describe earlier proposals rather than implemented behavior. Review original setup commands against the current repository before running them.

# Software Requirements Specification

## 1. Purpose

Define the functional and non-functional requirements for the Robotics Fleet Manager.

## 2. Scope

The initial system coordinates simulated autonomous mobile robots in a warehouse environment.

Physical robot integration, AI-driven planning, and advanced traffic optimization are future extensions.

## 3. Actors

- Administrator: manages users and system configuration.
- Fleet Operator: monitors robots and manages missions.
- Robot Simulator: produces robot telemetry and executes simulated commands.
- Fleet Scheduler: assigns eligible robots to missions.

## 4. Functional Requirements

### FR-001 Robot Registration
The system shall register robots with unique identifiers, capabilities, and operational status.

### FR-002 Robot Telemetry
The system shall accept timestamped robot telemetry, including position, battery, connectivity, and operating state.

### FR-003 Mission Creation
Operators shall be able to create missions with pickup and destination locations.

### FR-004 Mission Assignment
The scheduler shall assign eligible missions to available robots based on capability, battery, location, and availability.

### FR-005 Mission Lifecycle
The system shall track missions through defined states:
CREATED, QUEUED, ASSIGNED, RUNNING, COMPLETED, FAILED, and CANCELLED.

### FR-006 Connectivity Monitoring
The system shall identify robots that have stopped reporting telemetry.

### FR-007 Failure Recovery
The system shall support safe reassignment or operator intervention when a robot becomes unavailable.

### FR-008 Live Dashboard
The dashboard shall display robot and mission updates using WebSockets.

### FR-009 Audit Trail
The system shall record mission transitions, operator actions, and relevant system events.

### FR-010 Robot Simulation
The system shall support multiple simulated robots with configurable movement speeds, battery consumption, and failure scenarios.

## 5. Non-Functional Requirements

### NFR-001 Reliability
Mission state transitions must be validated and persistently recorded.

### NFR-002 Security
Protected operations must require authentication and appropriate authorization.

### NFR-003 Maintainability
The backend shall follow modular architecture principles with clear interfaces and automated tests.

### NFR-004 Observability
The platform shall provide structured logs, health checks, and operational metrics.

### NFR-005 Reproducibility
Python dependencies and environments shall be managed using Pixi and a committed lockfile.

### NFR-006 Performance
Initial development targets:
- 20 simulated robots
- 100 stored missions
- Dashboard updates approximately once per second

These are engineering targets, not verified benchmarks.

## 6. Out of Scope for MVP

- Certified safety-critical robot control
- Production ROS 2 integration
- Computer vision perception
- Physical robot navigation
- LLM-controlled safety decisions
- Multi-site fleet management

## 7. MVP Acceptance Criteria

- Register at least five simulated robots.
- Create missions through a documented API.
- Assign missions to eligible robots.
- Display simulated robot movement.
- Track mission completion and failure.
- Detect simulated offline robots.
- Persist mission history.
- Pass automated backend tests.
