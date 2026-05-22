"""add complexity to tasks

Revision ID: 20260522_0009
Revises: 20260522_0008
Create Date: 2026-05-22 18:10:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "20260522_0009"
down_revision = "20260522_0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "tasks",
        sa.Column(
            "complexity",
            sa.String(length=32),
            nullable=False,
            server_default=sa.text("'intermediate'"),
        ),
    )


def downgrade() -> None:
    op.drop_column("tasks", "complexity")
