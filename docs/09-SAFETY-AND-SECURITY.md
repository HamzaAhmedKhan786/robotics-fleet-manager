# Safety and Security Design — FleetOS

## 1. Scope

FleetOS is a **software simulation**, not a certified industrial fleet controller. Current local API endpoints are development tools; production authentication, policy enforcement and observability are not verified. Threat and safety reviews are required before exposing the service publicly or using physical robots.

## 2. Current rules

- Select available robots only, with valid start stations and enough estimated battery after completing the whole mission.
- Keep missions pending if no candidate can safely complete them.
- Track mission lifecycle and prevent double assignment through database transaction checks.
- Demo may queue missions but **must not create robots**.
- Target manual-only maximum of 15 registered robots; full backend enforcement and concurrency tests remain required.
- Simulated completion and battery estimates must never be interpreted as physical delivery confirmation.

## 3. Planned identity and authorization

Roles: administrator, fleet operator, read-only viewer and simulator/service identity. Authenticated permissions should govern robot registration, activation, mission cancellation, manual action endpoints, configuration and telemetry subscriptions. A loopback-only demo guard is not authentication. Use least privilege, secure secrets and separate service accounts.

## 4. Data and API security

- Keep `.env`, API keys and database passwords out of Git.
- TLS and secure cookies/tokens in deployment.
- Validate station identifiers, priorities, state transitions and payload sizes.
- Apply appropriate CORS allowlists and rate limits.
- Audit operator changes and security-relevant events.
- Protect against command replay and duplicate worker processing.
- Never let a chatbot's tool request bypass authorization or deterministic constraints.

## 5. Robotics safety boundary

Physical robots need independently validated protective stopping, emergency stop, obstacle detection, collision avoidance and local navigation. The current route visualization does **not** verify collision clearance or traffic safety. Simulated x/z positions, once persisted, still do not prove real-world localization accuracy.

## 6. Option B safety requirements

Constrain speed, timestep, map bounds, segment transitions and energy model; validate inputs at the Rust boundary. On database outage, do not emit a false success; on worker restart, reconcile persisted state. Later add route/edge reservations to prevent two simulated robots entering mutually exclusive corridor sections.

## 7. AI boundary (future)

AI agents can explain plans, draft missions and suggest schedule adjustments. Their outputs must be schema-validated and subject to permissions and explicit operator approval for impactful actions. No LLM should issue low-level motion commands, override emergency stops, or redefine hard battery restrictions.

## 8. Verification plan

Auth/permission tests, negative state transitions, double assignments, fleet cap under parallel registrations, unexpected worker termination, stale/duplicate telemetry, traffic overlap, unsafe battery estimates, prompt-injection attempts against tools, dependency scanning and penetration testing before deployment.

---

## Original specification retained for traceability (historical baseline)

> **Historical reference, not a statement of current implementation.** The original text below is preserved so that no early requirement, design option, setup explanation, or proposed feature is lost. Where it differs from the current sections above, **the current sections take precedence**. In particular, references to Next.js, 20 robots, WebSocket telemetry, continuous movement, Redis integration, A* navigation, authentication, or physical control may describe earlier proposals rather than implemented behavior. Review original setup commands against the current repository before running them.

# Safety and Security Design

## 1. Scope

This document describes planned application security and robotics safety boundaries.

The MVP is simulation-only and is not a certified industrial robot control system.

## 2. Application Security

### Authentication
- Authenticate operators and administrators.
- Use secure session or token management.
- Protect WebSocket connections.

### Authorization
Proposed roles:
- Administrator
- Fleet Operator
- Read-only Viewer
- Simulator Service

### Data Security
- Encrypt traffic in production.
- Keep secrets outside source control.
- Validate external input.
- Record security-relevant events.
- Apply least-privilege database permissions.

## 3. Robot Safety

The fleet manager must not replace robot-local safety mechanisms.

Physical robots must independently handle:
- Emergency stopping
- Obstacle detection
- Safe motion control
- Protective stopping
- Hardware faults

## 4. Operational Safety Rules

- Do not assign missions to unavailable robots.
- Prevent simultaneous conflicting reservations.
- Stop scheduling when critical dependencies are unavailable.
- Reject stale or invalid commands.
- Require acknowledgements for mission commands.
- Detect lost communication.
- Provide operator intervention workflows.

## 5. AI Safety Boundary

Future AI agents may recommend schedules or mission plans.

They must not directly override:
- Emergency stop conditions
- Robot safety controllers
- Restricted zones
- Hard battery limits
- Validated operational constraints

## 6. Security Testing

- Authentication tests
- Authorization tests
- Invalid command tests
- Replay and duplicate command tests
- Input validation tests
- Dependency vulnerability scanning

## 7. Production Readiness

Before physical deployment, perform a formal risk assessment and evaluate applicable robotics safety standards, regulations, and manufacturer requirements.
