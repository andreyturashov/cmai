from __future__ import annotations

from fastapi import FastAPI
from sqladmin import Admin
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from app.auth import SESSION_SECRET
from app.db import AsyncSessionFactory, engine

from .auth import SessionAdminAuth
from .task import TaskAdmin, TaskIssueAdmin
from .user import UserAdmin, UserProgressAdmin


def setup_admin(
    app: FastAPI,
    database_engine: AsyncEngine = engine,
    session_factory: async_sessionmaker[AsyncSession] = AsyncSessionFactory,
) -> Admin:
    app.state.admin_session_factory = session_factory
    admin = Admin(
        app,
        database_engine,
        title="Code Mentor Admin",
        authentication_backend=SessionAdminAuth(session_factory, SESSION_SECRET),
    )
    admin.add_view(UserAdmin)
    admin.add_view(UserProgressAdmin)
    admin.add_view(TaskAdmin)
    admin.add_view(TaskIssueAdmin)
    return admin


__all__ = ["setup_admin"]
