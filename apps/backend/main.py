"""Robotics Fleet Manager FastAPI application."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from apps.backend.api.fleet import router as fleet_router
from apps.backend.api.missions import router as missions_router
from apps.backend.api.robots import router as robots_router

app = FastAPI(
    title="Robotics Fleet Manager API",
    description="Fleet orchestration and robot simulation platform",
    version="0.2.0",
)

# Development-only frontend origins.
# Configure production CORS separately before deployment.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8501",
        "http://127.0.0.1:8501",
    ],
    allow_methods=["GET", "POST", "PATCH"],
    allow_headers=["Content-Type", "Authorization"],
)

app.include_router(robots_router)
app.include_router(missions_router)
app.include_router(fleet_router)


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {
        "status": "healthy",
        "service": "robotics-fleet-manager",
    }
