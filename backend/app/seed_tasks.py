from __future__ import annotations

import argparse
import asyncio

from sqlalchemy import delete, select
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


async def add_missing_seed_tasks(
    session_factory: async_sessionmaker[AsyncSession],
    tasks: list[Task] | None = None,
) -> int:
    tasks_to_seed = tasks or TASKS

    async with session_factory() as session:
        result = await session.execute(select(TaskRecord.id))
        existing_ids = set(result.scalars().all())
        missing_tasks = [task for task in tasks_to_seed if task.id not in existing_ids]

        if missing_tasks:
            session.add_all([_task_record_from_schema(task) for task in missing_tasks])
            await session.commit()

    return len(missing_tasks)


async def seed_from_static_data(*, replace: bool = False) -> None:
    if replace:
        count = await replace_seed_tasks(AsyncSessionFactory)
        print(f"Replaced tasks with {count} seeded items.")
    else:
        count = await add_missing_seed_tasks(AsyncSessionFactory)
        print(f"Added {count} new task(s) from static seed data.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed static tasks into the database.")
    parser.add_argument(
        "--replace",
        action="store_true",
        help="Replace all existing tasks instead of only adding missing seeded tasks.",
    )
    args = parser.parse_args()

    asyncio.run(seed_from_static_data(replace=args.replace))


if __name__ == "__main__":
    main()
