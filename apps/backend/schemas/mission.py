"""Pydantic schemas for mission API requests and responses."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from apps.backend.models.mission import MissionStatus


class MissionCreate(BaseModel):
    pickup_location: str = Field(min_length=1, max_length=100)
    delivery_location: str = Field(min_length=1, max_length=100)
    priority: int = Field(default=3, ge=1, le=5)


class MissionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    pickup_location: str
    delivery_location: str
    priority: int
    status: MissionStatus
    assigned_robot_id: UUID | None
    created_at: datetime
    updated_at: datetime
