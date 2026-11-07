# Robot Simulation Design — FleetOS

## 1. Objective

Exercise autonomous warehouse dispatch without physical robots, through deterministic mission planning and reproducible simulated execution. Distinguish **present mission-timer simulation** from **future authoritative continuous movement**.

## 2. Environment

Current warehouse graph has six stations: `STATION-A1`, `STATION-A2`, `STATION-A3`, `STATION-B1`, `STATION-B2`, `STATION-B3`. Weighted edges represent traversable links. UI maps these to Three.js x/z positions and draws racks outside primary aisles. Render geometry is illustrative; collision clearance has not been verified.

## 3. Current simulator behavior

The Python worker regularly:

1. Reads pending missions by priority and creation time.
2. Checks available robots, station location and battery reserve.
3. Plans a graph route from robot → pickup → destination.
4. Calls native Rust candidate selection.
5. Assigns and starts missions in PostgreSQL.
6. Marks in-progress missions completed once estimated duration elapses.
7. Deducts estimated battery and frees the robot (or changes to charging).

The dashboard's 3D carts estimate their position from mission start time and duration and slide along planned station segments. That movement **is browser visualization, not database-persisted telemetry**; any discrepancy during reload must not be treated as a backend position event.

## 4. Simulation parameters

Current Python plan has demonstration energy consumption per distance unit, a minimum safety reserve and a duration formula based on distance with a lower bound. These values are illustrative and should be centralized/configured; they are not measured motor or battery characteristics. Actual constants depend on the repository checkout.

## 5. Option B: authoritative movement engine (target)

Move deterministic movement stepping into Rust:

```text
advance(state, dt, route, speed) -> {
  x, z, segment_index, progress, energy_used, done
}
```

The backend owns the simulation clock and current state, persists each meaningful tick, and determines arrival and completion. The browser is only a renderer, interpolating between committed states. Protect against the worker being restarted while a mission is in progress and against duplicate completion/battery deductions.

## 6. Visualization goals

- Enlarged 3D map with floor grid, storage racks, clearly labeled stations, robot carts and hover/selection details.
- Distinct route color for each mission, with offsets where shared edges overlap.
- Moving cart orientation follows the segment tangent.
- Label progress as **simulated**. Unknown/offline robots should not appear as actively moving.
- Correctly distribute multiple parked robots at the same station and distinguish physical-position approximation from station occupancy.

## 7. Future traffic management

Current routes may share an edge at the same time. Collision avoidance **is not implemented**. Proposed route reservations and conflict handling: edge occupancy, time windows, deadlock detection, priorities and deterministic release on failure. Do not advertise the simulator as collision-free before tests validate those properties.

## 8. Failure scenarios and tests

No eligible robot, insufficient battery, missing station, disconnected graph, loss of worker, interrupted DB transaction, stale telemetry, duplicate tick and invalid mission state. Physical safety requires a separate robot-local system and independent validation.

---

## Original specification retained for traceability (historical baseline)

> **Historical reference, not a statement of current implementation.** The original text below is preserved so that no early requirement, design option, setup explanation, or proposed feature is lost. Where it differs from the current sections above, **the current sections take precedence**. In particular, references to Next.js, 20 robots, WebSocket telemetry, continuous movement, Redis integration, A* navigation, authentication, or physical control may describe earlier proposals rather than implemented behavior. Review original setup commands against the current repository before running them.

# Robot Simulation Design

## 1. Objective

Create a deterministic, reproducible warehouse robot simulator that can test fleet scheduling without physical robots.

## 2. Environment

The initial environment is a two-dimensional warehouse grid.

It includes:
- Robot starting locations
- Pickup locations
- Delivery locations
- Charging stations
- Obstacles
- Restricted zones

## 3. Robot Model

Each robot maintains:

- Unique ID
- Position
- Speed
- Battery percentage
- Payload capacity
- Operational status
- Active mission
- Last heartbeat

## 4. Simulation Loop

At each simulation tick:

1. Read the current robot state.
2. Process pending commands.
3. Update planned movement.
4. Apply simulated battery consumption.
5. Check mission progress.
6. Generate telemetry.
7. Publish events.

## 5. Navigation

Initial implementation:
- Grid-based navigation
- A* path planning
- Static obstacles
- Fixed simulation time steps

Future improvements:
- Dynamic obstacles
- Multi-robot path planning
- Traffic reservation
- Congestion-aware routing

## 6. Failure Injection

Supported test scenarios should include:

- Robot disconnect
- Low battery
- Mission timeout
- Blocked route
- Command acknowledgement delay
- Duplicate command delivery

## 7. Safety Limitations

The simulator does not prove that a real robot can safely execute the same commands.

Physical deployment requires additional safety engineering and hardware-level validation.
