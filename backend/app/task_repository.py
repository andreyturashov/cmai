from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db_models import TaskIssueRecord, TaskRecord
from app.models import Complexity, Issue, Severity, Task


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


def _task_from_record(task: TaskRecord) -> Task:
    return Task(
        id=task.id,
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

    async def list_tasks(self, language: str | None = None) -> list[Task]:
        stmt = (
            select(TaskRecord)
            .options(selectinload(TaskRecord.reference_issues))
            .order_by(TaskRecord.id)
        )
        if language:
            stmt = stmt.where(TaskRecord.language == language)

        records = (await self.session.scalars(stmt)).all()
        return [_task_from_record(record) for record in records]

    async def get_task(self, task_id: str) -> Task | None:
        stmt = (
            select(TaskRecord)
            .options(selectinload(TaskRecord.reference_issues))
            .where(TaskRecord.id == task_id)
        )
        record = await self.session.scalar(stmt)
        if record is None:
            return None
        return _task_from_record(record)

    async def list_tasks_for_languages(
        self,
        languages: list[str],
        *,
        exclude_task_ids: set[str] | None = None,
    ) -> list[Task]:
        if not languages:
            return []

        stmt = (
            select(TaskRecord)
            .options(selectinload(TaskRecord.reference_issues))
            .where(TaskRecord.language.in_(languages))
            .order_by(TaskRecord.id)
        )
        if exclude_task_ids:
            stmt = stmt.where(TaskRecord.id.not_in(exclude_task_ids))

        records = (await self.session.scalars(stmt)).all()
        return [_task_from_record(record) for record in records]

    async def list_tasks_by_ids(self, task_ids: list[str]) -> list[Task]:
        if not task_ids:
            return []

        stmt = (
            select(TaskRecord)
            .options(selectinload(TaskRecord.reference_issues))
            .where(TaskRecord.id.in_(task_ids))
        )
        records = (await self.session.scalars(stmt)).all()
        records_by_id = {record.id: record for record in records}
        ordered_records = [
            records_by_id[task_id] for task_id in task_ids if task_id in records_by_id
        ]
        return [_task_from_record(record) for record in ordered_records]
