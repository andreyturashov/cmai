from __future__ import annotations

import argparse
import asyncio

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import selectinload

from app.db import AsyncSessionFactory
from app.models import TaskIssueRecord, TaskRecord
from app.schemas import Task
from app.seed_data import TASKS


def _task_record_from_schema(task: Task) -> TaskRecord:
    return TaskRecord(
        id=task.id,
        title=task.title,
        description=task.description,
        language=task.language,
        complexity=task.complexity.value,
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


def _sync_task_record(record: TaskRecord, task: Task) -> None:
    record.title = task.title
    record.description = task.description
    record.language = task.language
    record.complexity = task.complexity.value
    record.submission_mode = task.submission_mode
    record.code = task.code
    record.requirements = task.requirements
    record.instructions = task.instructions
    record.reference_issues = [
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
    ]


async def _sync_seed_tasks(
    session_factory: async_sessionmaker[AsyncSession],
    tasks: list[Task],
) -> tuple[int, int]:
    async with session_factory() as session:
        existing_records = {
            record.id: record
            for record in (
                await session.scalars(
                    select(TaskRecord).options(selectinload(TaskRecord.reference_issues))
                )
            ).all()
        }

        added_count = 0
        updated_count = 0

        for task in tasks:
            record = existing_records.get(task.id)
            if record is None:
                session.add(_task_record_from_schema(task))
                added_count += 1
                continue

            _sync_task_record(record, task)
            updated_count += 1

        if added_count or updated_count:
            await session.commit()

    return added_count, updated_count


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
    added_count, _ = await _sync_seed_tasks(session_factory, tasks_to_seed)
    return added_count


async def seed_from_static_data(*, replace: bool = False) -> None:
    if replace:
        count = await replace_seed_tasks(AsyncSessionFactory)
        print(f"Replaced tasks with {count} seeded items.")
    else:
        added_count, updated_count = await _sync_seed_tasks(AsyncSessionFactory, TASKS)
        print(
            f"Added {added_count} new task(s) and synced {updated_count} existing task(s) from static seed data."
        )


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
