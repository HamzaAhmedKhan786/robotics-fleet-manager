
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
