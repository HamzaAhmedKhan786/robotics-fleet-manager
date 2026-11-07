"""Pydantic schemas for robot API requests and responses."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from apps.backend.models.robot import RobotStatus


class RobotCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    battery_level: float = Field(default=100.0, ge=0, le=100)
    current_location: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
    )


class RobotUpdate(BaseModel):
    """Operator-updated telemetry and non-busy operating state."""

    status: RobotStatus | None = None
    battery_level: float | None = Field(
        default=None,
        ge=0,
        le=100,
    )
    current_location: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
    )


class RobotResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    status: RobotStatus
    battery_level: float
    current_location: str | None
    position_x: float | None = None
    position_z: float | None = None
    movement_progress: float = 0.0
    position_updated_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
