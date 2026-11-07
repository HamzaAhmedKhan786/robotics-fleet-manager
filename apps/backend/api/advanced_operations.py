"""Development-simulator controls, telemetry and audited operator actions.

Set FLEETOS_OPERATOR_TOKEN to a strong secret; never expose this token to the
browser bundle. Integrate a proper identity provider before any public deploy.
"""
from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from apps.backend.db.session import AsyncSessionLocal, get_db
from apps.backend.models.mission import Mission, MissionStatus
from apps.backend.models.robot import Robot
from apps.backend.services.advanced_motion import STATIONS
from apps.backend.services.fleet_auth import require_role, verify_token

router = APIRouter(prefix="/api/v1/operations", tags=["Advanced fleet operations"])


DbSession = Annotated[AsyncSession, Depends(get_db)]
Operator = Annotated[str, Depends(require_role("operator"))]
Admin = Annotated[str, Depends(require_role("admin"))]


@router.post("/missions/{mission_id}/{action}")
async def mission_control(mission_id: UUID, action: str, session: DbSession, actor: Operator):
    if action not in ("pause", "resume", "restart"):
        raise HTTPException(422, "Allowed actions: pause, resume, restart")
    async with session.begin():
        mission = (await session.execute(select(Mission).where(Mission.id == mission_id).with_for_update())).scalar_one_or_none()
        if mission is None:
            raise HTTPException(404, "Mission not found")
        if mission.status != MissionStatus.IN_PROGRESS:
            raise HTTPException(409, "Only in-progress missions can be controlled")
        plan = dict(mission.plan or {})
        if action == "pause":
            plan["paused"] = True
        elif action == "resume":
            plan["paused"] = False
            plan["advanced_last_tick"] = datetime.now(UTC).isoformat()
        else:
            # Restart is strictly simulated; do not teleport into an occupied station.
            if not plan.get("paused", False):
                raise HTTPException(409, "Pause the mission before restarting")
            path = plan.get("path") or []
            origin = STATIONS.get(path[0]) if path else None
            if origin is None or mission.assigned_robot_id is None:
                raise HTTPException(409, "Mission has no valid restart origin")
            robots = list((await session.execute(select(Robot).order_by(Robot.id).with_for_update())).scalars().all())
            for other in robots:
                if (
                    other.id != mission.assigned_robot_id
                    and other.position_x is not None
                    and other.position_z is not None
                    and (
                        (other.position_x - origin[0]) ** 2
                        + (other.position_z - origin[1]) ** 2
                    ) ** 0.5 < 1.2
                ):
                    raise HTTPException(409, "Cannot restart: origin is occupied")
            robot = next(r for r in robots if r.id == mission.assigned_robot_id)
            robot.position_x, robot.position_z = origin
            robot.movement_progress = 0.0
            robot.position_updated_at = datetime.now(UTC)
            plan["advanced_elapsed"] = 0.0
            plan["advanced_last_tick"] = datetime.now(UTC).isoformat()
            plan["paused"] = False
        mission.plan = plan
        await session.execute(text("""
            INSERT INTO fleet_audit_events(actor, action, resource, details)
            VALUES (:actor, :action, :resource, '{}'::jsonb)
        """), {"actor": actor, "action": action, "resource": str(mission_id)})
    return {"id": str(mission_id), "action": action, "accepted": True}


@router.get("/robots/{robot_id}/history")
async def position_history(robot_id: UUID, session: DbSession, actor: Operator, limit: int = 250):
    limit = max(1, min(1000, limit))
    result = await session.execute(text("""
        SELECT id, mission_id, position_x, position_z, velocity, progress, event_type, recorded_at
        FROM robot_position_events WHERE robot_id = :robot
        ORDER BY id DESC LIMIT :limit
    """), {"robot": robot_id, "limit": limit})
    return [dict(row) for row in result.mappings().all()][::-1]


@router.get("/audit")
async def audit_history(session: DbSession, actor: Admin, limit: int = 100):
    limit = max(1, min(500, limit))
    result = await session.execute(text("""
        SELECT id, actor, action, resource, details, created_at
        FROM fleet_audit_events ORDER BY id DESC LIMIT :limit
    """), {"limit": limit})
    return [dict(row) for row in result.mappings().all()]


@router.get("/worker")
async def worker_status(session: DbSession, actor: Operator):
    row = (await session.execute(text(
        "SELECT owner, heartbeat_at FROM fleet_worker_status WHERE id = 1"
    ))).mappings().first()
    if row is None:
        return {"owner": None, "heartbeat_at": None, "running": False}
    # Heartbeat shows recent successful coordinated ticks; not absolute liveness.
    return {"owner": row["owner"], "heartbeat_at": row["heartbeat_at"],
            "running": (datetime.now(UTC) - row["heartbeat_at"]).total_seconds() < 5}


@router.websocket("/ws/telemetry")
async def websocket_telemetry(socket: WebSocket):
    # First-message authentication avoids bearer tokens in URLs and access logs.
    await socket.accept()
    try:
        received = await asyncio.wait_for(socket.receive_json(), timeout=5)
        try:
            verify_token(str(received.get("token", "")))
        except HTTPException:
            await socket.close(code=1008, reason="Unauthorized")
            return
        while True:
            async with AsyncSessionLocal() as session:
                rows = (await session.execute(text("""
                    SELECT id::text AS id, name, status::text AS status,
                           position_x, position_z, movement_progress,
                           position_updated_at FROM robots ORDER BY name
                """))).mappings().all()
                result = [{**dict(row), "position_updated_at": row["position_updated_at"].isoformat() if row["position_updated_at"] else None} for row in rows]
            await socket.send_json({"type": "fleet.snapshot", "robots": result})
            await asyncio.sleep(1.0)
    except WebSocketDisconnect:
        # The peer has already disconnected; sending another close raises.
        return
    except TimeoutError:
        # Initial authentication timed out. The connection may already be gone.
        try:
            await socket.close(code=1008, reason="Authentication timed out")
        except WebSocketDisconnect:
            pass
