
"""Robotics Fleet Manager API with local autonomous dispatcher."""

import asyncio
import logging
import os
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from apps.backend.api.advanced_operations import router as advanced_router
from apps.backend.api.demo import router as demo_router
from apps.backend.api.fleet import router as fleet_router
from apps.backend.api.fleet_identity import router as identity_router
from apps.backend.api.missions import router as missions_router
from apps.backend.api.robots import router as robots_router
from apps.backend.core.config import settings
from scripts.auto_worker import main as worker_main

logger = logging.getLogger(__name__)

dispatcher_task: asyncio.Task[None] | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Start and stop the autonomous dispatcher with FastAPI."""

    global dispatcher_task

    enabled = (
        settings.simulation_enabled
        and settings.app_env == "development"
        and settings.postgres_db != "robotics_fleet_test"
    )

    if enabled:
        dispatcher_task = asyncio.create_task(
            worker_main(),
            name="autonomous-fleet-dispatcher",
        )
        logger.info("Autonomous dispatcher task started.")
    else:
        logger.info("Autonomous dispatcher disabled.")

    try:
        yield
    finally:
        if dispatcher_task is not None:
            dispatcher_task.cancel()

            with suppress(asyncio.CancelledError):
                await dispatcher_task

            dispatcher_task = None

        logger.info("Autonomous dispatcher stopped.")


app = FastAPI(
    title="Robotics Fleet Manager API",
    description="Autonomous robot fleet orchestration and simulation",
    version="0.4.0",
    lifespan=lifespan,
)

@app.middleware("http")
async def enforce_mutation_auth(request, call_next):
    from fastapi.responses import JSONResponse

    from apps.backend.services.fleet_auth import ROLES, verify_token
    if (os.environ.get("FLEETOS_REQUIRE_AUTH") == "1"
            and request.url.path.startswith("/api/v1/")
            and request.url.path != "/api/v1/auth/login"
            and request.method != "OPTIONS"):
        header = request.headers.get("authorization", "")
        if not header.startswith("Bearer "):
            return JSONResponse({"detail": "Bearer token required"}, status_code=401)
        try:
            claims = verify_token(header[7:])
        except HTTPException:
            return JSONResponse({"detail": "Invalid token"}, status_code=401)
        required = "viewer" if request.method in ("GET", "HEAD") else "operator"
        if ROLES[claims["role"]] < ROLES[required]:
            return JSONResponse({"detail": "Insufficient role"}, status_code=403)
    response = await call_next(request)
    if (os.environ.get("FLEETOS_REQUIRE_AUTH") == "1"
            and request.url.path.startswith("/api/v1/")
            and request.method in ("POST", "PATCH", "PUT", "DELETE")):
        from sqlalchemy import text

        from apps.backend.db.session import AsyncSessionLocal
        header = request.headers.get("authorization", "")
        actor = "unknown"
        if header.startswith("Bearer "):
            try:
                actor = verify_token(header[7:])["username"]
            except HTTPException:
                actor = "unknown"
        try:
            async with AsyncSessionLocal() as audit_session, audit_session.begin():
                await audit_session.execute(text(
                    "INSERT INTO fleet_audit_events(actor, action, resource) "
                    "VALUES (:actor, :action, :resource)"
                ), {
                    "actor": actor,
                    "action": request.method,
                    "resource": request.url.path[:150],
                })
        except Exception:
            logger.exception("Audit trail insertion failed; investigate database")
    return response


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_methods=["GET", "POST", "PATCH"],
    allow_headers=["Content-Type", "Authorization"],
)

app.include_router(robots_router)
app.include_router(missions_router)
app.include_router(fleet_router)
app.include_router(demo_router)
app.include_router(advanced_router)
app.include_router(identity_router)


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {
        "status": "healthy",
        "service": "robotics-fleet-manager",
    }


@app.get("/api/v1/system/dispatcher")
async def dispatcher_status() -> dict:
    """Report whether the local autonomous worker is alive."""

    task = dispatcher_task
    running = task is not None and not task.done()

    return {
        "running": running,
        "simulation_enabled": settings.simulation_enabled,
        "environment": settings.app_env,
        "database": settings.postgres_db,
        "mode": "local_simulation",
    }
