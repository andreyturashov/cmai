"""add user interests to users

Revision ID: 20260520_0006
Revises: 20260520_0005
Create Date: 2026-05-20 14:20:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "20260520_0006"
down_revision = "20260520_0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("user_interests", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
    )


def downgrade() -> None:
    op.drop_column("users", "user_interests")
