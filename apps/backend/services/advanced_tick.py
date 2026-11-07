"""Transactional simulation tick with conservative traffic coordination.

Call advance_running() only under the PostgreSQL advisory lock acquired
by scripts.auto_worker. All movements are simulated, not safety-rated.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

from sqlalchemy import select, text

from apps.backend.db.session import AsyncSessionLocal
from apps.backend.models.mission import Mission, MissionStatus
from apps.backend.models.robot import Robot
from apps.backend.services.advanced_motion import sample_segments
from apps.backend.services.traffic_control import (
    MoveIntent,
    arbitrate,
    segment_separation,
)

if TYPE_CHECKING:
    from apps.backend.services.advanced_motion import MotionSample

MAX_TICK_SECONDS = 2.0
RESERVATION_SECONDS = 1.2
MIN_CLEARANCE = 1.2
DEADLOCK_WARNING_TICKS = 20


def _safe_delta(last_tick: object, now: datetime) -> float:
    """Limit clock jumps; never catch up by teleporting a robot."""
    if not isinstance(last_tick, str) or not last_tick:
        return min(MAX_TICK_SECONDS, 1.0)
    try:
        timestamp = datetime.fromisoformat(last_tick)
    except ValueError:
        # Corrupt or legacy checkpoint: do not jump forward in time.
        return 0.0
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=UTC)
    return min(MAX_TICK_SECONDS, max(0.0, (now - timestamp).total_seconds()))


def _stable_arbitration(
    intents: list[MoveIntent],
    occupied: dict[str, tuple[float, float]],
    reservations: list[MoveIntent],
) -> tuple[list[MoveIntent], list[MoveIntent]]:
    """Block conflicting segments and recursively treat held robots as obstacles.

    A newly held robot remains at its old location. Consequently, accepting a
    move that passes that location may become unsafe; re-evaluate to a fixed
    point before writing any new coordinates. This is conservative and can
    leave robots waiting at a congestion point.
    """
    blocked_ids = {
        intent.robot_id
        for intent in intents
        if any(
            prior.robot_id != intent.robot_id
            and segment_separation(intent, prior) < MIN_CLEARANCE
            for prior in reservations
        )
    }
    candidates = [intent for intent in intents if intent.robot_id not in blocked_ids]
    admitted, rejected = arbitrate(candidates, occupied, clearance=MIN_CLEARANCE)
    blocked_ids.update(intent.robot_id for intent in rejected)

    # All robots not moving are stationary obstacles, including those without
    # a movement intent (offline, idle, charging and held robots).
    while True:
        stationary = {
            robot_id: position
            for robot_id, position in occupied.items()
            if robot_id not in {intent.robot_id for intent in admitted}
        }
        newly_blocked = {
            intent.robot_id
            for intent in admitted
            if any(
                segment_separation(
                    intent, MoveIntent(robot_id, position, position)
                ) < MIN_CLEARANCE
                for robot_id, position in stationary.items()
                if robot_id != intent.robot_id
            )
        }
        if not newly_blocked:
            break
        blocked_ids.update(newly_blocked)
        admitted = [
            intent for intent in admitted if intent.robot_id not in newly_blocked
        ]

    accepted_ids = {intent.robot_id for intent in admitted}
    waiting = [intent for intent in intents if intent.robot_id not in accepted_ids]
    return admitted, waiting


async def advance_running() -> None:
    """Advance at most one collision-screened snapshot per active mission.

    The single transaction locks missions and robots in deterministic order,
    validates short-lived aisle reservations, and writes positions and history
    together. Keep the outer worker advisory lock in place for multi-process
    deployments; row locks alone do not serialize every simulation tick.
    """
    now = datetime.now(UTC)

    async with AsyncSessionLocal() as session, session.begin():
        mission_rows = await session.execute(
            select(Mission)
            .where(Mission.status == MissionStatus.IN_PROGRESS)
            .order_by(Mission.priority.desc(), Mission.id)
            .with_for_update()
        )
        running = list(mission_rows.scalars().all())

        robot_rows = await session.execute(
            select(Robot).order_by(Robot.id).with_for_update()
        )
        robots = list(robot_rows.scalars().all())
        robot_by_id = {robot.id: robot for robot in robots}
        occupied = {
            str(robot.id): (robot.position_x, robot.position_z)
            for robot in robots
            if robot.position_x is not None and robot.position_z is not None
        }

        intents: list[MoveIntent] = []
        samples: dict[str, tuple[Mission, Robot, MotionSample]] = {}
        elapsed_by_robot: dict[str, float] = {}

        for mission in running:
            robot_id = mission.assigned_robot_id
            if robot_id is None:
                continue
            robot = robot_by_id.get(robot_id)
            if robot is None:
                continue

            plan = mission.plan or {}
            path = plan.get("path") or []
            if not path or bool(plan.get("paused", False)):
                continue

            key = str(robot.id)
            if key in samples:
                # A robot must not advance two missions in a single tick.
                # The assignment service should enforce this invariant.
                raise ValueError(f"Multiple running missions assigned to robot {key}")

            previous = max(0.0, float(plan.get("advanced_elapsed", 0.0)))
            delta = _safe_delta(plan.get("advanced_last_tick"), now)
            elapsed = previous + delta
            sample = sample_segments(path, elapsed)
            origin = occupied.get(key)
            if origin is None:
                start_sample = sample_segments(path, previous)
                origin = (start_sample.x, start_sample.z)
                occupied[key] = origin

            intents.append(
                MoveIntent(key, origin, (sample.x, sample.z), mission.priority)
            )
            samples[key] = (mission, robot, sample)
            elapsed_by_robot[key] = elapsed

        # Remove expired reservations, then read live reservations from other
        # robots. Existing reservations of the same robot are ignored during
        # arbitration and replaced if its next movement is accepted.
        await session.execute(
            text("DELETE FROM fleet_aisle_reservations WHERE expires_at <= :now"),
            {"now": now},
        )
        reservation_rows = await session.execute(
            text(
                """
                SELECT robot_id, origin_x, origin_z, target_x, target_z
                FROM fleet_aisle_reservations
                WHERE expires_at > :now
                """
            ),
            {"now": now},
        )
        reservations = [
            MoveIntent(
                str(row["robot_id"]),
                (row["origin_x"], row["origin_z"]),
                (row["target_x"], row["target_z"]),
            )
            for row in reservation_rows.mappings().all()
        ]
        accepted, waiting = _stable_arbitration(intents, occupied, reservations)

        for intent in accepted:
            mission, robot, sample = samples[intent.robot_id]
            plan = dict(mission.plan or {})
            plan["advanced_last_tick"] = now.isoformat()
            plan["advanced_elapsed"] = elapsed_by_robot[intent.robot_id]
            plan["traffic_state"] = "moving"
            plan["traffic_wait_ticks"] = 0
            plan.pop("traffic_alert", None)

            robot.position_x = sample.x
            robot.position_z = sample.z
            robot.movement_progress = sample.progress
            robot.position_updated_at = now

            # Replace this robot's previous reservation rather than leaving
            # overlapping rows that can accumulate across fast simulation ticks.
            await session.execute(
                text("DELETE FROM fleet_aisle_reservations WHERE robot_id = :robot"),
                {"robot": robot.id},
            )
            await session.execute(
                text(
                    """
                    INSERT INTO fleet_aisle_reservations
                      (robot_id, mission_id, origin_x, origin_z,
                       target_x, target_z, expires_at)
                    VALUES
                      (:robot, :mission, :ox, :oz, :tx, :tz, :expiry)
                    """
                ),
                {
                    "robot": robot.id,
                    "mission": mission.id,
                    "ox": intent.origin[0],
                    "oz": intent.origin[1],
                    "tx": intent.target[0],
                    "tz": intent.target[1],
                    "expiry": now + timedelta(seconds=RESERVATION_SECONDS),
                },
            )
            await session.execute(
                text(
                    """
                    INSERT INTO robot_position_events
                      (robot_id, mission_id, position_x, position_z,
                       velocity, progress, event_type)
                    VALUES
                      (:robot, :mission, :x, :z, :v, :progress, 'movement')
                    """
                ),
                {
                    "robot": robot.id,
                    "mission": mission.id,
                    "x": sample.x,
                    "z": sample.z,
                    "v": sample.speed,
                    "progress": sample.progress,
                },
            )
            mission.plan = plan

        for intent in waiting:
            mission, _, _ = samples[intent.robot_id]
            plan = dict(mission.plan or {})
            # Waiting must not accumulate elapsed simulation time.
            plan["advanced_last_tick"] = now.isoformat()
            plan["traffic_state"] = "waiting"
            wait_ticks = int(plan.get("traffic_wait_ticks", 0)) + 1
            plan["traffic_wait_ticks"] = wait_ticks
            if wait_ticks >= DEADLOCK_WARNING_TICKS:
                plan["traffic_alert"] = "potential_deadlock_requires_operator_review"
            mission.plan = plan
