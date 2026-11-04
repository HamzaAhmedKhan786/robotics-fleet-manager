
from fastapi import FastAPI

app = FastAPI(
    title="Robotics Fleet Manager API",
    description="Fleet orchestration and robot simulation platform",
    version="0.1.0",
)


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {
        "status": "healthy",
        "service": "robotics-fleet-manager",
    }


@app.get("/api/v1/fleet/summary")
async def fleet_summary() -> dict[str, int]:
    return {
        "total_robots": 0,
        "active_robots": 0,
        "active_missions": 0,
    }
