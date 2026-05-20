"""add ai analysis to progress

Revision ID: 20260520_0005
Revises: 20260520_0004
Create Date: 2026-05-20 14:00:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "20260520_0005"
down_revision = "20260520_0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("user_progress", sa.Column("ai_analysis", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("user_progress", "ai_analysis")
