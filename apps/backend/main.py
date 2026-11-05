"""Robotics Fleet Manager FastAPI application."""

from fastapi import FastAPI

from apps.backend.api.robots import router as robots_router

app = FastAPI(
    title="Robotics Fleet Manager API",
    description="Fleet orchestration and robot simulation platform",
    version="0.1.0",
)

app.include_router(robots_router)


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {
        "status": "healthy",
        "service": "robotics-fleet-manager",
    }


@app.get("/api/v1/fleet/summary")
async def fleet_summary() -> dict[str, int]:
    """Placeholder until fleet aggregation is implemented."""
    return {
        "total_robots": 0,
        "active_robots": 0,
        "active_missions": 0,
    }
