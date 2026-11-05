# ADR 0002 — Local Development Infrastructure

**Status:** Accepted

**Date:** 2026-11-05

## Context

Robotics Fleet Manager requires persistent PostgreSQL storage and plans to use Redis for temporary state and event distribution.

The primary development machine runs Windows 11 with 8 GB RAM. Running a full Docker Desktop development stack can cause resource contention and reduced responsiveness.

PostgreSQL 18 is already installed locally, and connectivity to the `robotics_fleet` database has been verified.

## Decision

Adopt a hybrid local development setup:

- Run FastAPI and the robot simulator through Pixi.
- Use the existing native PostgreSQL installation.
- Run Redis as a standalone Docker service when required.
- Retain Docker Compose configuration for reproducible infrastructure.
- Keep environment-specific connection settings outside application business logic.

## Alternatives considered

### Full Docker Compose stack

Provides consistent containerized infrastructure but introduces additional resource overhead on the development machine.

### Entirely native Windows services

Avoids Docker overhead but introduces additional installation and compatibility requirements for Redis.

### Managed cloud infrastructure

Reduces local resource usage but introduces network dependencies, external service configuration, and potential costs.

### SQLite instead of PostgreSQL

Simplifies local setup but differs from the intended PostgreSQL transaction and concurrency behavior used by the fleet management system.

## Consequences

### Benefits

- Reuses the existing PostgreSQL installation.
- Avoids running duplicate database servers.
- Preserves the planned application architecture.
- Supports development on resource-constrained hardware.
- Allows containerized infrastructure in other environments.

### Trade-offs

- Local infrastructure is not identical to a fully containerized deployment.
- Docker Desktop still introduces overhead when Redis is running.
- Developers must ensure PostgreSQL is running separately.
- Additional integration testing may be required to validate deployment-specific behavior.

## Review criteria

Revisit this decision if the development environment changes, the application requires additional infrastructure services, or container-based development becomes practical.