"""Robot persistence model."""

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum,
    Float,
    String,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from apps.backend.db.base import Base


class RobotStatus(str, enum.Enum):
    OFFLINE = "offline"
    AVAILABLE = "available"
    BUSY = "busy"
    CHARGING = "charging"
    ERROR = "error"


class Robot(Base):
    __tablename__ = "robots"

    __table_args__ = (
        CheckConstraint(
            "battery_level >= 0 AND battery_level <= 100",
            name="ck_robots_battery_level",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    name: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
    )

    status: Mapped[RobotStatus] = mapped_column(
        Enum(
            RobotStatus,
            name="robot_status",
            values_callable=lambda enum_cls: [item.value for item in enum_cls],
        ),
        default=RobotStatus.OFFLINE,
        nullable=False,
    )

    battery_level: Mapped[float] = mapped_column(
        Float,
        default=100.0,
        nullable=False,
    )

    current_location: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
