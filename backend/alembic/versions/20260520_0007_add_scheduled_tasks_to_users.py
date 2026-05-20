"""add scheduled tasks to users

Revision ID: 20260520_0007
Revises: 20260520_0006
Create Date: 2026-05-20 15:00:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "20260520_0007"
down_revision = "20260520_0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "scheduled_task_ids",
            sa.JSON(),
            nullable=False,
            server_default=sa.text("'[]'"),
        ),
    )


def downgrade() -> None:
    op.drop_column("users", "scheduled_task_ids")
