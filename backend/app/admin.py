from __future__ import annotations

from fastapi import FastAPI
from sqladmin import Admin, ModelView
from sqlalchemy.ext.asyncio import AsyncEngine

from app.db import engine
from app.db_models import TaskIssueRecord, TaskRecord


class TaskAdmin(ModelView, model=TaskRecord):
    name = "Task"
    name_plural = "Tasks"
    icon = "fa-solid fa-list-check"
    category = "Content"

    column_list = [
        TaskRecord.id,
        TaskRecord.title,
        TaskRecord.language,
        TaskRecord.submission_mode,
        TaskRecord.created_at,
        TaskRecord.updated_at,
    ]
    column_details_list = "__all__"
    column_searchable_list = [TaskRecord.id, TaskRecord.title, TaskRecord.language]
    column_sortable_list = [
        TaskRecord.id,
        TaskRecord.title,
        TaskRecord.language,
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


def setup_admin(app: FastAPI, database_engine: AsyncEngine = engine) -> Admin:
    admin = Admin(app, database_engine, title="Code Mentor Admin")
    admin.add_view(TaskAdmin)
    admin.add_view(TaskIssueAdmin)
    return admin
