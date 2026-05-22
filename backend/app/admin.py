from __future__ import annotations

from fastapi import FastAPI
from sqladmin import Admin, ModelView
from sqladmin.authentication import AuthenticationBackend
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker
from starlette.requests import Request
from starlette.responses import PlainTextResponse, Response

from app.auth import SESSION_SECRET
from app.db import AsyncSessionFactory, engine
from app.db_models import TaskIssueRecord, TaskRecord, UserProgressRecord, UserRecord


class SessionAdminAuth(AuthenticationBackend):
    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        secret_key: str,
    ) -> None:
        super().__init__(secret_key=secret_key)
        self.session_factory = session_factory

    async def login(self, request: Request) -> bool:
        return False

    async def logout(self, request: Request) -> Response | bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> Response | bool:
        user_id = request.session.get("user_id")
        if not user_id:
            return PlainTextResponse(
                "Admin access requires a signed-in admin user.", status_code=403
            )

        session_factory = getattr(request.app.state, "admin_session_factory", self.session_factory)
        async with session_factory() as session:
            user = await session.get(UserRecord, user_id)

        if user is None or not user.is_admin:
            return PlainTextResponse(
                "Admin access requires a signed-in admin user.", status_code=403
            )

        return True


class UserAdmin(ModelView, model=UserRecord):
    name = "User"
    name_plural = "Users"
    icon = "fa-solid fa-user"
    category = "Users"

    column_list = [
        UserRecord.id,
        UserRecord.email,
        UserRecord.name,
        UserRecord.is_admin,
        UserRecord.google_sub,
        UserRecord.created_at,
        UserRecord.updated_at,
    ]
    column_details_list = "__all__"
    column_searchable_list = [
        UserRecord.id,
        UserRecord.email,
        UserRecord.name,
        UserRecord.google_sub,
    ]
    column_sortable_list = [
        UserRecord.id,
        UserRecord.email,
        UserRecord.name,
        UserRecord.is_admin,
        UserRecord.created_at,
        UserRecord.updated_at,
    ]
    column_default_sort = [(UserRecord.updated_at, True)]
    form_excluded_columns = [UserRecord.created_at, UserRecord.updated_at]
    page_size = 25
    page_size_options = [25, 50, 100]


class TaskAdmin(ModelView, model=TaskRecord):
    name = "Task"
    name_plural = "Tasks"
    icon = "fa-solid fa-list-check"
    category = "Content"

    column_list = [
        TaskRecord.id,
        TaskRecord.title,
        TaskRecord.language,
        TaskRecord.complexity,
        TaskRecord.submission_mode,
        TaskRecord.created_at,
        TaskRecord.updated_at,
    ]
    column_details_list = "__all__"
    column_searchable_list = [
        TaskRecord.id,
        TaskRecord.title,
        TaskRecord.language,
        TaskRecord.complexity,
    ]
    column_sortable_list = [
        TaskRecord.id,
        TaskRecord.title,
        TaskRecord.language,
        TaskRecord.complexity,
        TaskRecord.created_at,
        TaskRecord.updated_at,
    ]
    column_default_sort = [(TaskRecord.updated_at, True)]
    form_excluded_columns = [TaskRecord.created_at, TaskRecord.updated_at]
    page_size = 25
    page_size_options = [25, 50, 100]


class TaskIssueAdmin(ModelView, model=TaskIssueRecord):
    name = "Task Issue"
    name_plural = "Task Issues"
    icon = "fa-solid fa-triangle-exclamation"
    category = "Content"

    column_list = [
        TaskIssueRecord.id,
        TaskIssueRecord.task_id,
        TaskIssueRecord.sort_order,
        TaskIssueRecord.line,
        TaskIssueRecord.severity,
        TaskIssueRecord.title,
    ]
    column_details_list = "__all__"
    column_searchable_list = [
        TaskIssueRecord.id,
        TaskIssueRecord.task_id,
        TaskIssueRecord.title,
        TaskIssueRecord.severity,
    ]
    column_sortable_list = [
        TaskIssueRecord.task_id,
        TaskIssueRecord.sort_order,
        TaskIssueRecord.line,
        TaskIssueRecord.severity,
    ]
    column_default_sort = [
        (TaskIssueRecord.task_id, False),
        (TaskIssueRecord.sort_order, False),
    ]
    page_size = 50
    page_size_options = [25, 50, 100]


class UserProgressAdmin(ModelView, model=UserProgressRecord):
    name = "User Progress"
    name_plural = "User Progress"
    icon = "fa-solid fa-chart-line"
    category = "Users"

    column_list = [
        UserProgressRecord.id,
        UserProgressRecord.user_id,
        UserProgressRecord.task_id,
        UserProgressRecord.score,
        UserProgressRecord.submission_count,
        UserProgressRecord.updated_at,
    ]
    column_details_list = "__all__"
    column_searchable_list = [
        UserProgressRecord.user_id,
        UserProgressRecord.task_id,
        UserProgressRecord.user_answer,
        UserProgressRecord.suggestion,
    ]
    column_sortable_list = [
        UserProgressRecord.user_id,
        UserProgressRecord.task_id,
        UserProgressRecord.score,
        UserProgressRecord.submission_count,
        UserProgressRecord.created_at,
        UserProgressRecord.updated_at,
    ]
    column_default_sort = [(UserProgressRecord.updated_at, True)]
    form_excluded_columns = [
        UserProgressRecord.created_at,
        UserProgressRecord.updated_at,
    ]
    page_size = 50
    page_size_options = [25, 50, 100]


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
