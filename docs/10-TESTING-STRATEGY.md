
# Testing Strategy

## 1. Objectives

Validate business logic, mission consistency, simulation behavior, security, and failure recovery.

## 2. Unit Tests

Test:
- Robot eligibility
- Mission state transitions
- Battery calculations
- Scheduling scores
- Pathfinding
- Command validation

Framework: Pytest

## 3. Integration Tests

Test:
- FastAPI and PostgreSQL
- Database migrations
- Scheduler transactions
- Redis integration
- Simulator communication

## 4. API Tests

Test:
- Successful requests
- Invalid input
- Unauthorized access
- Missing resources
- Conflicting mission assignments
- Idempotent operations

## 5. End-to-End Tests

Framework: Playwright

Scenarios:
1. Open dashboard.
2. Register a simulated robot.
3. Create a mission.
4. Observe assignment.
5. Monitor movement.
6. Verify completion.
7. Inspect mission history.

## 6. Failure Tests

- Robot disconnect
- Delayed telemetry
- Duplicate messages
- Database interruption
- Scheduler restart
- Mission cancellation
- Insufficient battery
- Blocked route

## 7. Performance Tests

Initial targets:
- 20 simulated robots
- One telemetry update per robot per second
- Five concurrent missions

Measure:
- API latency
- Scheduler processing time
- WebSocket delivery delay
- Database query performance
- CPU and memory utilization

## 8. CI Pipeline

Planned GitHub Actions checks:
- Ruff linting
- Pyright type checking
- Pytest
- Frontend ESLint
- TypeScript checking
- Playwright tests
- Dependency vulnerability checks

No test results should be reported until the tests have actually run.
