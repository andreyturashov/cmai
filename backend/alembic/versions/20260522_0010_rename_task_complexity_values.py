"""rename task complexity values

Revision ID: 20260522_0010
Revises: 20260522_0009
Create Date: 2026-05-22 17:55:00.000000
"""

# pyright: reportAttributeAccessIssue=false

from __future__ import annotations

from typing import cast

import sqlalchemy as sa

from alembic import op
from alembic.operations import Operations

revision = "20260522_0010"
down_revision = "20260522_0009"
branch_labels = None
depends_on = None


def _ops() -> Operations:
    return cast(Operations, op)


def upgrade() -> None:
    operations = _ops()
    operations.execute(
        sa.text("UPDATE tasks SET complexity = 'easy' WHERE complexity = 'beginner'")
    )
    operations.execute(
        sa.text("UPDATE tasks SET complexity = 'medium' WHERE complexity = 'intermediate'")
    )
    operations.execute(
        sa.text("UPDATE tasks SET complexity = 'hard' WHERE complexity = 'advanced'")
    )
    operations.alter_column(
        "tasks",
        "complexity",
        existing_type=sa.String(length=32),
        server_default=sa.text("'medium'"),
    )


def downgrade() -> None:
    operations = _ops()
    operations.execute(
        sa.text("UPDATE tasks SET complexity = 'beginner' WHERE complexity = 'easy'")
    )
    operations.execute(
        sa.text("UPDATE tasks SET complexity = 'intermediate' WHERE complexity = 'medium'")
    )
    operations.execute(
        sa.text("UPDATE tasks SET complexity = 'advanced' WHERE complexity = 'hard'")
    )
    operations.alter_column(
        "tasks",
        "complexity",
        existing_type=sa.String(length=32),
        server_default=sa.text("'intermediate'"),
    )
