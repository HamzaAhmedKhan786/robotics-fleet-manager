# ADR-0001 — Technology Stack

**Status:** Accepted and amended 2026-11-07  
**Original proposal:** 2026-11-04

## Context

FleetOS needs a manageable, testable robotics orchestration prototype with persistent mission state, native computation, 3D visualization and repeatable development. The originally proposed Next.js frontend and Redis/WebSocket architecture were **not** the implementation eventually chosen for the local prototype.

## Decision — implemented

1. **Frontend:** React + TypeScript + Vite, not Next.js. Use Three.js through React Three Fiber and Drei for 3D scene; a 2D graph remains available.
2. **Backend:** FastAPI + Pydantic for HTTP, schemas and lifecycle integration.
3. **Persistence:** PostgreSQL + SQLAlchemy 2 async + Alembic + asyncpg; mission and robot state are durable.
4. **Native scheduling:** Rust extension via PyO3 and Maturin. Current role is deterministic candidate ranking; Python still computes routes and energy. Target expansion is Rust graph/energy/simulation engine.
5. **Worker:** Python asyncio scheduling loop (single instance in local development).
6. **Environment:** Pixi for Python tools/dependencies and lockfile; npm for frontend.
7. **Validation:** Pytest, Ruff, Pyright and TypeScript/Vite build. Rust unit/benchmark suites to grow with Option B.

## Deferred decisions

- Redis for cache, events or distributed coordination only if measured needs justify it; not required locally.
- WebSockets/SSE for pushed robot telemetry once persisted movement exists; current frontend polls REST.
- ROS 2/MQTT for later physical integration, not in present MVP.
- Optional LLM integration for operator assistance, never motion safety authority.

## Alternatives considered

Next.js (unnecessary SSR for a local dashboard), frontend-only simulation (fails authoritative-state requirement), Python-only engine (simpler, but less opportunity for native simulation), separate Rust service (greater deployment complexity), RabbitMQ/Redis versus PostgreSQL-backed polling (unnecessary for six-node local prototype).

## Consequences

**Benefits:** clear Python orchestration/native-compute split; fast operator UI development; PostgreSQL consistency; realistic digital-twin presentation; testable path to Rust core and Option B.  
**Trade-offs:** Python/Rust boundary and rebuild overhead, separate Node toolchain, local worker lifecycle complexity, presentation animations not yet telemetry, future distributed coordination design.

## Review conditions

Revisit when target fleet workload, streaming throughput, real-world ROS integration or traffic constraints require different operational architecture. Measure native vs Python performance before claiming improvement.

---

## Original specification retained for traceability (historical baseline)

> **Historical reference, not a statement of current implementation.** The original text below is preserved so that no early requirement, design option, setup explanation, or proposed feature is lost. Where it differs from the current sections above, **the current sections take precedence**. In particular, references to Next.js, 20 robots, WebSocket telemetry, continuous movement, Redis integration, A* navigation, authentication, or physical control may describe earlier proposals rather than implemented behavior. Review original setup commands against the current repository before running them.

# ADR-0001: Technology Stack

**Status:** Proposed
**Date:** 2026-11-04

## Context

The project requires a maintainable robotics orchestration platform with simulation, real-time monitoring, and reproducible development environments.

## Decision

### Frontend: Next.js and TypeScript
Selected for component-based development, routing, dashboard interfaces, and strong TypeScript support.

### Backend: FastAPI
Selected for Python integration, Pydantic validation, OpenAPI documentation, and asynchronous interfaces.

### Python Environment: Pixi
Selected to evaluate reproducible environments, cross-platform dependency management, lockfiles, and task definitions.

### Database: PostgreSQL
Selected for transactional consistency, relational data, and reliable mission persistence.

### Cache and Coordination: Redis
Selected for transient coordination, caching, and event notifications.

### Robot Simulation: Python
Selected for rapid prototyping, testability, and compatibility with the backend ecosystem.

### Robot Integration: ROS 2 (Future)
ROS 2 is a candidate for future robot communication and interoperability. It is not required for the initial Windows-based simulation.

## Alternatives Considered

- Django instead of FastAPI
- React with Vite instead of Next.js
- Poetry or uv instead of Pixi
- RabbitMQ instead of Redis for messaging
- Microservices instead of a modular monolith

## Consequences

Benefits:
- Familiar development ecosystem
- Clear architectural boundaries
- Reproducible Python dependencies
- Fast initial development

Trade-offs:
- Multiple runtime environments
- Additional database and cache operations
- Future ROS 2 integration complexity
- Need for robust distributed-state coordination

## Review

Reevaluate technology choices after completing the MVP and measuring operational requirements.
