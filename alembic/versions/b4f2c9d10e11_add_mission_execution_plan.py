"""Add autonomous mission planning fields.

Revision ID: b4f2c9d10e11
Revises: 8f74e2cbf143
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

from alembic import op

revision: str = "b4f2c9d10e11"
down_revision: str | Sequence[str] | None = "8f74e2cbf143"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "missions",
        sa.Column("plan", JSONB(), nullable=True),
    )
    op.add_column(
        "missions",
        sa.Column("selection_reason", sa.Text(), nullable=True),
    )
    op.add_column(
        "missions",
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )
    op.add_column(
        "missions",
        sa.Column(
            "finished_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("missions", "finished_at")
    op.drop_column("missions", "started_at")
    op.drop_column("missions", "selection_reason")
    op.drop_column("missions", "plan")
