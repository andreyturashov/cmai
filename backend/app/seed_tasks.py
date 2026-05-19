from __future__ import annotations

import asyncio

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.db import AsyncSessionFactory
from app.db_models import TaskIssueRecord, TaskRecord
from app.models import Task
from app.seed_data import TASKS


def _task_record_from_schema(task: Task) -> TaskRecord:
    return TaskRecord(
        id=task.id,
        title=task.title,
        description=task.description,
        language=task.language,
        submission_mode=task.submission_mode,
        code=task.code,
        requirements=task.requirements,
        instructions=task.instructions,
        reference_issues=[
            TaskIssueRecord(
                id=issue.id,
                task_id=task.id,
                sort_order=index,
                line=issue.line,
                severity=issue.severity.value,
                title=issue.title,
                description=issue.description,
                suggestion=issue.suggestion,
                code=issue.code,
            )
            for index, issue in enumerate(task.reference_issues)
        ],
    )


async def replace_seed_tasks(
    session_factory: async_sessionmaker[AsyncSession],
    tasks: list[Task] | None = None,
) -> int:
    tasks_to_seed = tasks or TASKS

    async with session_factory() as session:
        await session.execute(delete(TaskIssueRecord))
        await session.execute(delete(TaskRecord))
        session.add_all([_task_record_from_schema(task) for task in tasks_to_seed])
        await session.commit()

    return len(tasks_to_seed)


async def seed_from_static_data() -> None:
    count = await replace_seed_tasks(AsyncSessionFactory)
    print(f"Seeded {count} tasks into the database.")


def main() -> None:
    asyncio.run(seed_from_static_data())


if __name__ == "__main__":
    main()
