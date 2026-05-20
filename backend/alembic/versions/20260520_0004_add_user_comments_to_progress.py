"""add user comments to progress

Revision ID: 20260520_0004
Revises: 20260519_0003
Create Date: 2026-05-20 13:25:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "20260520_0004"
down_revision = "20260519_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "user_progress",
        sa.Column("user_comments", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
    )


def downgrade() -> None:
    op.drop_column("user_progress", "user_comments")
