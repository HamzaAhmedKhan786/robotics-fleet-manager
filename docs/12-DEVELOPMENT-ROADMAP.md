# Development Roadmap — FleetOS

**Updated:** 2026-11-07. Status reflects demonstrated work and documented source; unchecked items are not claimed implemented.

## Phase 0 — Repository and foundation

- [x] Git repository and initial project documents
- [x] Pixi/Python environment
- [x] FastAPI application and health endpoint
- [x] PostgreSQL development DB and connectivity
- [x] SQLAlchemy async models and Alembic migrations
- [x] Separate integration-test database
- [ ] Enforce branch protection and mandatory CI checks

## Phase 1 — Fleet and mission APIs

- [x] Robot registration and operating state management
- [x] Mission creation, cancellation and lifecycle transitions
- [x] Persisted robot and mission records
- [x] Fleet summary and warehouse topology endpoints
- [x] Automated backend tests (historically 39 passed locally)
- [ ] Fully verify 15-robot cap under concurrent manual registrations
- [ ] Authentication and role-based registration permissions

## Phase 2 — Autonomous orchestration

- [x] Persistent pending mission queue
- [x] Python weighted warehouse graph and route planning
- [x] Estimated battery feasibility and reserve constraint
- [x] Compiled Rust/PyO3 deterministic candidate selection
- [x] Autonomous Python worker assigns, starts and time-completes missions
- [x] Store selection explanation and planned route
- [x] Mission-only demo flow (no robot auto-provisioning)
- [ ] Robust multi-process worker ownership, retries and fault recovery

## Phase 3 — Frontend and digital twin

- [x] React/TypeScript/Vite dashboard
- [x] Fleet cards, battery gauges, station/status details
- [x] Mission queue, search and history
- [x] 2D warehouse graph and per-mission routes
- [x] Three.js / R3F digital twin with shelves, stations and orange AMR carts
- [x] Camera orbit, zoom and select cart
- [x] Mission-time-based visual interpolation
- [ ] Persist actual simulated x/z positions from the backend
- [ ] Backend-driven movement, progress and timestamp visualization

## Phase 4 — Option B: Rust-powered simulation (next)

- [ ] Define graph/coordinate and simulation time contracts
- [ ] Rust weighted pathfinding and route concatenation
- [ ] Rust configurable battery-feasibility engine
- [ ] Rust deterministic per-tick cart motion and heading
- [ ] Expose typed PyO3 result structures and Rust unit tests
- [ ] Alembic migration for authoritative positions/progress
- [ ] Python worker calls Rust and commits movement samples
- [ ] Frontend interpolates committed samples (never drives completion)
- [ ] Worker restart and idempotency/concurrency tests
- [ ] Document Rust/Python performance measurements, not assumptions

## Phase 5 — Scheduling safety and reliability

- [ ] Shared-edge corridor reservations and traffic avoidance
- [ ] Deadlock/failure injection and recovery
- [ ] Durable audit/mission event history
- [ ] Event streaming (WebSocket/SSE) with access control
- [ ] Auth, roles, rate limiting and security scans
- [ ] CI/CD, load tests, container images, staging environment

## Phase 6 — Optional agentic AI

- [ ] Natural-language mission tool with validated stations and schemas
- [ ] Fleet diagnostic/operations-explanation assistant
- [ ] Human approval for mission modifications
- [ ] Optional local Ollama or hosted LLM provider abstraction
- [ ] Tool execution audit, prompt-injection and privilege tests

## Future

- ROS 2 adapters, physical telemetry, charging scheduler, multi-robot optimization and production safety validation

## Definition of done

A feature is done only when code is committed, tests and builds pass, docs describe the current behavior honestly, error states are handled and security/safety constraints are reviewed.

---

## Original specification retained for traceability (historical baseline)

> **Historical reference, not a statement of current implementation.** The original text below is preserved so that no early requirement, design option, setup explanation, or proposed feature is lost. Where it differs from the current sections above, **the current sections take precedence**. In particular, references to Next.js, 20 robots, WebSocket telemetry, continuous movement, Redis integration, A* navigation, authentication, or physical control may describe earlier proposals rather than implemented behavior. Review original setup commands against the current repository before running them.

# Development Roadmap

## Phase 0 — Repository and Documentation

- [ ] Create GitHub repository
- [ ] Add README
- [ ] Add architecture documentation
- [ ] Add requirements specification
- [ ] Add system design
- [ ] Add contribution guidelines
- [ ] Configure GitHub branch protection

## Phase 1 — Development Environment

- [ ] Install Pixi
- [ ] Create pixi.toml
- [ ] Generate pixi.lock
- [ ] Initialize FastAPI backend
- [ ] Initialize Next.js frontend
- [ ] Configure PostgreSQL
- [ ] Configure Redis
- [ ] Configure Docker Compose

## Phase 2 — Backend Foundation

- [ ] Define database models
- [ ] Configure Alembic migrations
- [ ] Implement robot registry
- [ ] Implement mission CRUD
- [ ] Implement state validation
- [ ] Add structured logging
- [ ] Add API tests

## Phase 3 — Robot Simulator

- [ ] Define warehouse grid
- [ ] Implement simulated robots
- [ ] Implement movement
- [ ] Implement battery consumption
- [ ] Implement telemetry
- [ ] Implement heartbeat monitoring
- [ ] Add fault injection

## Phase 4 — Fleet Orchestration

- [ ] Implement mission scheduler
- [ ] Add robot eligibility filtering
- [ ] Add atomic reservations
- [ ] Add command acknowledgements
- [ ] Add mission recovery
- [ ] Add basic traffic coordination

## Phase 5 — Frontend

- [ ] Build dashboard layout
- [ ] Add robot overview
- [ ] Add mission management
- [ ] Add warehouse visualization
- [ ] Add WebSocket updates
- [ ] Add operational alerts

## Phase 6 — Reliability

- [ ] Implement authentication
- [ ] Implement authorization
- [ ] Add audit logging
- [ ] Add integration tests
- [ ] Add Playwright tests
- [ ] Add metrics
- [ ] Add CI/CD

## Phase 7 — Advanced Capabilities

- [ ] Add optimized batch scheduling
- [ ] Evaluate ROS 2 integration
- [ ] Evaluate MQTT integration
- [ ] Add advanced simulation scenarios
- [ ] Evaluate AI-assisted mission planning

## Definition of Done

A feature is complete when:
- Implementation is committed.
- Automated tests pass.
- Documentation is updated.
- Error handling is verified.
- Security implications are reviewed.
- Relevant acceptance criteria are satisfied.
