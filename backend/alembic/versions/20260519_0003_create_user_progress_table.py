"""create user progress table

Revision ID: 20260519_0003
Revises: 20260519_0002
Create Date: 2026-05-19 01:10:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "20260519_0003"
down_revision = "20260519_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "user_progress",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("task_id", sa.String(length=128), nullable=False),
        sa.Column("score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("suggestion", sa.Text(), nullable=False, server_default=""),
        sa.Column("user_answer", sa.Text(), nullable=False, server_default=""),
        sa.Column("submission_count", sa.Integer(), nullable=False, server_default="1"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["task_id"], ["tasks.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "task_id", name="uq_user_progress_user_task"),
    )
    op.create_index(op.f("ix_user_progress_user_id"), "user_progress", ["user_id"], unique=False)
    op.create_index(op.f("ix_user_progress_task_id"), "user_progress", ["task_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_user_progress_task_id"), table_name="user_progress")
    op.drop_index(op.f("ix_user_progress_user_id"), table_name="user_progress")
    op.drop_table("user_progress")
