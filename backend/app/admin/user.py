from __future__ import annotations

from sqladmin import ModelView

from app.models import UserProgressRecord, UserRecord


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
