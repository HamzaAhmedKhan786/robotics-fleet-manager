
# Database Design

## 1. Database

PostgreSQL is the authoritative persistence layer.

SQLAlchemy manages database models and Alembic manages schema migrations.

## 2. Entity Relationship Diagram

```mermaid
erDiagram
    ROBOTS ||--o{ ROBOT_TELEMETRY : produces
    ROBOTS ||--o{ MISSIONS : assigned_to
    MISSIONS ||--o{ MISSION_EVENTS : generates
    USERS ||--o{ AUDIT_LOGS : performs

    ROBOTS {
        uuid id PK
        string name
        string type
        string status
        integer battery_percent
        datetime last_seen_at
    }

    MISSIONS {
        uuid id PK
        uuid robot_id FK
        string status
        integer priority
        json pickup
        json destination
        datetime created_at
    }

    ROBOT_TELEMETRY {
        uuid id PK
        uuid robot_id FK
        float position_x
        float position_y
        integer battery_percent
        datetime recorded_at
    }

    MISSION_EVENTS {
        uuid id PK
        uuid mission_id FK
        string event_type
        json payload
        datetime created_at
    }

    USERS {
        uuid id PK
        string email
        string role
    }

    AUDIT_LOGS {
        uuid id PK
        uuid user_id FK
        string action
        datetime created_at
    }
```

## 3. Data Integrity

- Use UUID primary keys.
- Apply foreign key constraints.
- Validate mission state transitions in application logic.
- Add database constraints for valid battery ranges.
- Index robot status and mission status.
- Index telemetry by robot ID and timestamp.
- Prevent multiple active assignments for the same robot.

## 4. Transactions

Mission assignment must be atomic.

The transaction should:
1. Lock the selected robot.
2. Confirm availability.
3. Reserve the robot.
4. Assign the mission.
5. Record an event.
6. Commit.

External commands should be dispatched after durable persistence, preferably through a transactional outbox pattern.

## 5. Retention

Telemetry retention and archival policies will be defined before production deployment.

Mission and audit history should have separate retention policies.
