"""Add movement events and operational audit trail.

Revision ID: f20261107b001
Revises: e20261107a001
"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

from alembic import op

revision: str = "f20261107b001"
down_revision: str | Sequence[str] | None = "e20261107a001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "robot_position_events",
        sa.Column("id", sa.BigInteger(), sa.Identity(), primary_key=True),
        sa.Column("robot_id", UUID(as_uuid=True), sa.ForeignKey("robots.id", ondelete="CASCADE"), nullable=False),
        sa.Column("mission_id", UUID(as_uuid=True), sa.ForeignKey("missions.id", ondelete="SET NULL")),
        sa.Column("position_x", sa.Float(), nullable=False),
        sa.Column("position_z", sa.Float(), nullable=False),
        sa.Column("velocity", sa.Float(), nullable=False),
        sa.Column("progress", sa.Float(), nullable=False),
        sa.Column("event_type", sa.String(32), nullable=False, server_default="movement"),
        sa.Column("recorded_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_position_events_robot_time", "robot_position_events", ["robot_id", "recorded_at"])
    op.create_table(
        "fleet_audit_events",
        sa.Column("id", sa.BigInteger(), sa.Identity(), primary_key=True),
        sa.Column("actor", sa.String(100), nullable=False),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("resource", sa.String(150), nullable=False),
        sa.Column("details", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_fleet_audit_time", "fleet_audit_events", ["created_at"])
    op.create_table(
        "fleet_aisle_reservations",
        sa.Column("id", sa.BigInteger(), sa.Identity(), primary_key=True),
        sa.Column("robot_id", UUID(as_uuid=True), sa.ForeignKey("robots.id", ondelete="CASCADE"), nullable=False),
        sa.Column("mission_id", UUID(as_uuid=True), sa.ForeignKey("missions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("origin_x", sa.Float(), nullable=False),
        sa.Column("origin_z", sa.Float(), nullable=False),
        sa.Column("target_x", sa.Float(), nullable=False),
        sa.Column("target_z", sa.Float(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_aisle_reservation_expiry", "fleet_aisle_reservations", ["expires_at"])
    op.create_table(
        "fleet_worker_status",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("owner", sa.String(160), nullable=False),
        sa.Column("heartbeat_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("id = 1", name="ck_fleet_worker_singleton"),
    )
    op.create_table(
        "fleet_users",
        sa.Column("username", sa.String(80), primary_key=True),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column("role", sa.String(16), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("role IN ('viewer','operator','admin')", name="ck_fleet_users_role"),
    )


def downgrade() -> None:
    op.drop_table("fleet_users")
    op.drop_table("fleet_worker_status")
    op.drop_index("ix_aisle_reservation_expiry", table_name="fleet_aisle_reservations")
    op.drop_table("fleet_aisle_reservations")
    op.drop_index("ix_fleet_audit_time", table_name="fleet_audit_events")
    op.drop_table("fleet_audit_events")
    op.drop_index("ix_position_events_robot_time", table_name="robot_position_events")
    op.drop_table("robot_position_events")
