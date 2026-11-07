
"""Local autonomous demonstration.

Create missions using existing fleet robots.
Never provision robots automatically.
"""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, ConfigDict
from sqlalchemy import func, select

from apps.backend.core.config import settings
from apps.backend.db.session import AsyncSessionLocal
from apps.backend.models.mission import Mission
from apps.backend.models.robot import Robot

router = APIRouter(
    prefix="/api/v1/demo",
    tags=["Demo"],
)

MAX_FLEET_SIZE = 15


class DemoOptions(BaseModel):
    """Demo options kept for backward compatibility."""

    model_config = ConfigDict(extra="forbid")

    auto_provision: bool = False


@router.post("/simulation")
async def start_demo_simulation(
    request: Request,
    options: DemoOptions | None = None,
):
    """Queue two missions for the autonomous fleet worker."""

    host = request.client.host if request.client else ""

    if (
        settings.app_env != "development"
        or host not in ("127.0.0.1", "::1")
    ):
        raise HTTPException(
            status_code=403,
            detail="Local development only.",
        )

    options = options or DemoOptions()

    # Users must register robots manually.
    if options.auto_provision:
        raise HTTPException(
            status_code=422,
            detail=(
                "Automatic robot provisioning is disabled. "
                "Only users can register robots manually."
            ),
        )

    async with AsyncSessionLocal() as session, session.begin():

        robot_count = (
            await session.scalar(
                select(func.count()).select_from(Robot)
            )
        ) or 0

        mission_a = Mission(
            pickup_location="STATION-A2",
            delivery_location="STATION-B1",
            priority=4,
        )

        mission_b = Mission(
            pickup_location="STATION-B2",
            delivery_location="STATION-A3",
            priority=3,
        )

        session.add_all([mission_a, mission_b])
        await session.flush()

        mission_ids = [
            str(mission_a.id),
            str(mission_b.id),
        ]

    return {
        "message": (
            "Two missions queued. Existing eligible robots "
            "will be selected automatically. If all robots "
            "are busy or none can safely complete a mission, "
            "it remains pending until a suitable robot "
            "becomes available."
        ),
        "mission_ids": mission_ids,
        "missions_created": 2,
        "robots_created": 0,
        "total_robots": robot_count,
        "max_robots": MAX_FLEET_SIZE,
        "auto_provision": False,
    }
