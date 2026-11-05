"""Pydantic schemas for robot API requests and responses."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from apps.backend.models.robot import RobotStatus


class RobotCreate(BaseModel):
    """Data required to register a robot."""

    name: str = Field(min_length=1, max_length=100)
    battery_level: float = Field(default=100.0, ge=0, le=100)


class RobotResponse(BaseModel):
    """Robot data returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    status: RobotStatus
    battery_level: float
    created_at: datetime
    updated_at: datetime
