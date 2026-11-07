"""Persist authoritative simulated X/Z positions and progress.

Revision ID: e20261107a001
Revises: b4f2c9d10e11
"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "e20261107a001"
down_revision: str | Sequence[str] | None = "b4f2c9d10e11"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("robots", sa.Column("position_x", sa.Float(), nullable=True))
    op.add_column("robots", sa.Column("position_z", sa.Float(), nullable=True))
    op.add_column(
        "robots",
        sa.Column("movement_progress", sa.Float(), nullable=False, server_default="0"),
    )
    op.add_column(
        "robots", sa.Column("position_updated_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.create_check_constraint(
        "ck_robots_movement_progress", "robots",
        "movement_progress >= 0 AND movement_progress <= 1",
    )
    # Keep existing robots visible immediately after deployment.
    op.execute("""
        UPDATE robots SET
          position_x = CASE current_location
            WHEN 'STATION-A1' THEN -6 WHEN 'STATION-A2' THEN 0
            WHEN 'STATION-A3' THEN 6 WHEN 'STATION-B1' THEN -6
            WHEN 'STATION-B2' THEN 0 WHEN 'STATION-B3' THEN 6
            ELSE NULL END,
          position_z = CASE current_location
            WHEN 'STATION-A1' THEN -4 WHEN 'STATION-A2' THEN -4
            WHEN 'STATION-A3' THEN -4 WHEN 'STATION-B1' THEN 4
            WHEN 'STATION-B2' THEN 4 WHEN 'STATION-B3' THEN 4
            ELSE NULL END
    """)


def downgrade() -> None:
    op.drop_constraint("ck_robots_movement_progress", "robots", type_="check")
    op.drop_column("robots", "position_updated_at")
    op.drop_column("robots", "movement_progress")
    op.drop_column("robots", "position_z")
    op.drop_column("robots", "position_x")
