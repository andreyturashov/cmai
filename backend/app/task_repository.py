from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import TaskIssueRecord, TaskRecord, UserProgressRecord
from app.schemas import Complexity, Issue, Severity, Task


def _issue_from_record(issue: TaskIssueRecord) -> Issue:
    return Issue(
        id=issue.id,
        line=issue.line,
        severity=Severity(issue.severity),
        title=issue.title,
        description=issue.description,
        suggestion=issue.suggestion,
        code=issue.code,
    )


def _task_from_record(task: TaskRecord, is_completed: bool = False) -> Task:
    return Task(
        id=task.id,
        is_completed=is_completed,
        title=task.title,
        description=task.description,
        requirements=list(task.requirements or []),
        instructions=list(task.instructions or []),
        language=task.language,
        complexity=Complexity(task.complexity),
        submission_mode=task.submission_mode,
        code=task.code,
        reference_issues=[_issue_from_record(issue) for issue in task.reference_issues],
    )


class TaskRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_tasks(
        self,
        user_id: int | None = None,
        language: str | None = None,
        complexity: str | None = None,
    ) -> list[Task]:
        tasks_query = (
            select(TaskRecord)
            .options(selectinload(TaskRecord.reference_issues))
            .order_by(TaskRecord.id)
        )
        if language:
            tasks_query = tasks_query.where(TaskRecord.language == language)
        if complexity:
            tasks_query = tasks_query.where(TaskRecord.complexity == complexity)

        tasks = (await self.session.scalars(tasks_query)).all()

        if user_id is None:
            return [_task_from_record(record) for record in tasks]

        user_progress_query = select(UserProgressRecord).where(
            UserProgressRecord.task_id.in_([t.id for t in tasks]),
            UserProgressRecord.user_id == user_id,
        )
        completed_task_ids = {t.task_id for t in await self.session.scalars(user_progress_query)}

        return [
            _task_from_record(record, is_completed=record.id in completed_task_ids)
            for record in tasks
        ]

    async def get_task(self, task_id: str) -> Task | None:
        tasks_query = (
            select(TaskRecord)
            .options(selectinload(TaskRecord.reference_issues))
            .where(TaskRecord.id == task_id)
        )
        task = await self.session.scalar(tasks_query)

        user_progress_query = select(UserProgressRecord).where(
            UserProgressRecord.task_id == task_id,
        )
        user_progress = await self.session.scalar(user_progress_query)

        if task is None:
            return None

        return _task_from_record(task, is_completed=user_progress is not None)

    async def list_tasks_for_languages(
        self,
        languages: list[str],
        *,
        user_id: int | None = None,
        exclude_task_ids: set[str] | None = None,
    ) -> list[Task]:
        if not languages:
            return []

        tasks_query = (
            select(TaskRecord)
            .options(selectinload(TaskRecord.reference_issues))
            .where(TaskRecord.language.in_(languages))
            .order_by(TaskRecord.id)
        )
        if exclude_task_ids:
            tasks_query = tasks_query.where(TaskRecord.id.not_in(exclude_task_ids))

        tasks = (await self.session.scalars(tasks_query)).all()

        user_progress_query = select(UserProgressRecord).where(
            UserProgressRecord.task_id.in_([t.id for t in tasks]),
            UserProgressRecord.user_id == user_id,
        )
        completed_task_ids = {t.task_id for t in await self.session.scalars(user_progress_query)}

        return [_task_from_record(t, is_completed=t.id in completed_task_ids) for t in tasks]

    async def list_tasks_by_ids(self, user_id: int, task_ids: list[str]) -> list[Task]:
        if not task_ids:
            return []

        tasks_query = (
            select(TaskRecord)
            .options(selectinload(TaskRecord.reference_issues))
            .where(TaskRecord.id.in_(task_ids))
        )
        tasks = (await self.session.scalars(tasks_query)).all()
        # Preserve the order of task_ids as provided by the caller
        task_map = {t.id: t for t in tasks}
        existing_ids = [tid for tid in task_ids if tid in task_map]

        user_progress_tasks_query = select(UserProgressRecord).where(
            UserProgressRecord.task_id.in_(existing_ids),
            UserProgressRecord.user_id == user_id,
        )

        completed_task_ids = {
            record.task_id for record in await self.session.scalars(user_progress_tasks_query)
        }

        return [
            _task_from_record(task_map[tid], tid in completed_task_ids) for tid in existing_ids
        ]
