# Mission Scheduling and Fleet Optimization — FleetOS

## 1. Goal

Assign each queued warehouse mission to an existing eligible robot using deterministic route/battery constraints, transparent explanations and persistent state changes. Autonomous means rule-driven here; no learned agent chooses robot motion.

## 2. Implemented candidate filtering

Mission includes pickup, delivery and priority. The current planner estimates complete robot-start → pickup → delivery route using Python's warehouse graph; battery consumption must leave a fixed reserve. Robots must be available and have a valid station. Infeasible candidates are excluded before native ranking. Availability may change during computation, so assignment needs transaction-time revalidation.

## 3. Current Rust ranking

`fleet_scheduler.select_robot` accepts candidate tuples containing robot ID, availability, distance to pickup and battery. It prefers:

1. Minimum travel distance to pickup.
2. Higher battery when distances are equal.
3. Stable lexicographical identifier when still tied.

Python presently supplies the distances and feasibility. Rust currently **does not** compute Dijkstra paths, energy estimates, traffic reservations or continuous movement.

## 4. Queue and capacity

- Pending missions are scanned in descending priority, then age order.
- If no feasible robot exists, the mission remains pending and is reconsidered later.
- Releasing a robot permits queued jobs to dispatch on the next worker cycle.
- Demo only creates missions; it must not register robots.
- Fleet target cap is 15 manually registered robots. This number constrains robot registrations, **not the length of the queue**.

## 5. Mission lifecycle

`pending` → `assigned` → `in_progress` → `completed` in the normal automatic flow. `cancelled`/`failed` exist for appropriate negative outcomes. Store selected robot, planned station path, distance and energy estimate, selection reason, start/finish times. Manual lifecycle endpoints may be available for debugging but are not needed for normal demo operation.

## 6. Concurrency and correctness

Treat reservation as an atomic transaction. Lock the mission and selected robot or use equivalent conflict handling, and recheck availability immediately before marking busy. Ensure no two simultaneously active missions use one robot. Duplicate completion must not deduct battery twice. A multi-worker production deployment requires explicit queue ownership/leases.

## 7. Option B Rust responsibilities (target)

| Module | Target functionality |
|---|---|
| `graph.rs` | Warehouse graph validation and weighted paths |
| `routing.rs` | Shortest path from robot→pickup→delivery |
| `energy.rs` | Configurable energy cost and safety margin |
| `scheduler.rs` | Eligibility and candidate ranking |
| `simulation.rs` | Deterministic x/z movement advancement |
| `traffic.rs` | Shared aisle/time-window reservations (later) |

Rust should return decision and reason codes; Python handles authorization, transactions and published API. Benchmark both FFI overhead and actual useful work; six nodes/fifteen robots are not by themselves evidence of Rust speed advantage.

## 8. Future optimizations

Batch assignment, demand forecasting, deadlock-free traffic routing, charging scheduling, fault recovery and optional AI recommendations. AI output must pass deterministic validation before generating missions.

## 9. Suggested test cases

Equal-distance tie with higher battery; stable UUID tie; unreachable pickup; battery under reserve; robot becomes busy during assignment; all 15 robots busy; mission-only demo leaves robot count unchanged; worker restarts mid-job; duplicate completion and overlapping routes.

---

## Original specification retained for traceability (historical baseline)

> **Historical reference, not a statement of current implementation.** The original text below is preserved so that no early requirement, design option, setup explanation, or proposed feature is lost. Where it differs from the current sections above, **the current sections take precedence**. In particular, references to Next.js, 20 robots, WebSocket telemetry, continuous movement, Redis integration, A* navigation, authentication, or physical control may describe earlier proposals rather than implemented behavior. Review original setup commands against the current repository before running them.

# Mission Scheduling and Fleet Optimization

## 1. Objective

Assign warehouse missions to suitable robots while maintaining operational reliability.

## 2. Initial Scheduling Strategy

Use a deterministic, battery-aware, distance-based scheduler.

Eligibility requirements:
- Robot is IDLE.
- Robot is connected.
- Robot has required capabilities.
- Robot has sufficient battery.
- Robot is not already reserved.
- The mission can be executed under configured constraints.

## 3. Candidate Ranking

An initial scoring function may use:

```text
score =
    travel_distance_weight * estimated_distance
  + battery_weight * battery_penalty
  + congestion_weight * congestion_penalty
```

Lower scores indicate preferred candidates.

Mission priority determines queue ordering rather than bypassing safety and eligibility checks.

## 4. Scheduling Algorithm

```python
def select_robot(mission, robots):
    eligible = [
        robot
        for robot in robots
        if robot.status == "IDLE"
        and robot.is_connected
        and robot.supports(mission.required_capabilities)
        and robot.has_sufficient_battery(mission)
    ]

    if not eligible:
        return None

    return min(
        eligible,
        key=lambda robot: estimate_mission_cost(robot, mission),
    )
```

This is conceptual pseudocode, not an implemented scheduler.

## 5. Concurrency

Robot reservation must be atomic.

Multiple scheduler instances must not assign the same robot simultaneously.

## 6. Optimization Metrics

- Mission completion rate
- Average mission duration
- Robot utilization
- Idle time
- Energy consumption
- Failed assignments
- Queue waiting time

## 7. Future Algorithms

- Hungarian algorithm for batch assignment
- Constraint programming
- Multi-agent path finding
- Dynamic task reassignment
- Predictive maintenance
- AI-assisted planning

AI recommendations must remain subject to deterministic validation.
