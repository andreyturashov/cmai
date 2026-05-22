from __future__ import annotations

import random
from typing import Annotated
from uuid import uuid4

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from starlette.middleware.sessions import SessionMiddleware

from app.admin import setup_admin
from app.ai_analyzer import analyze_review
from app.auth import (
    GOOGLE_CLIENT_ID,
    SESSION_SECRET,
    get_cors_origins,
    is_bootstrap_admin_email,
    verify_google_credential,
)
from app.db import get_session
from app.db_models import TaskRecord, UserProgressRecord, UserRecord
from app.evaluator import evaluate_review
from app.models import (
    AuthenticatedUser,
    AuthSession,
    EvaluationRequest,
    GoogleLoginRequest,
    Issue,
    ReviewCreate,
    ScheduledTaskEntry,
    TaskScheduleResponse,
    UserInterestsResponse,
    UserInterestsUpdate,
    UserProgressDailySummary,
    UserProgressEntry,
    UserProgressTaskSummary,
    UserReview,
)
from app.task_repository import TaskRepository

load_dotenv()

app = FastAPI(title="Code Mentor API", version="0.1.0")

app.add_middleware(SessionMiddleware, secret_key=SESSION_SECRET, same_site="lax")
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

admin = setup_admin(app)

TASK_SCHEDULE_LIMIT = 10

REVIEWS: dict[str, UserReview] = {}


SessionDependency = Annotated[AsyncSession, Depends(get_session)]


def get_task_repository(session: SessionDependency) -> TaskRepository:
    return TaskRepository(session)


TaskRepositoryDependency = Annotated[TaskRepository, Depends(get_task_repository)]


def serialize_user(user: UserRecord) -> AuthenticatedUser:
    return AuthenticatedUser(
        id=user.id,
        email=user.email,
        name=user.name,
        avatar_url=user.avatar_url,
    )


def serialize_scheduled_tasks(tasks: list) -> TaskScheduleResponse:
    return TaskScheduleResponse(
        tasks=[
            ScheduledTaskEntry(
                id=task.id,
                title=task.title,
                description=task.description,
                requirements=task.requirements,
                instructions=task.instructions,
                language=task.language,
                complexity=task.complexity,
                submission_mode=task.submission_mode,
            )
            for task in tasks
        ]
    )


async def generate_and_store_task_schedule(
    *,
    current_user: UserRecord,
    session: AsyncSession,
    task_repository: TaskRepository,
) -> TaskScheduleResponse:
    interests = list(current_user.user_interests or [])
    if not interests:
        current_user.scheduled_task_ids = []
        await session.commit()
        return TaskScheduleResponse(tasks=[])

    completed_task_ids = set(
        (
            await session.execute(
                select(UserProgressRecord.task_id).where(
                    UserProgressRecord.user_id == current_user.id
                )
            )
        ).scalars()
    )

    candidate_tasks = await task_repository.list_tasks_for_languages(
        interests,
        exclude_task_ids=completed_task_ids,
    )
    random.shuffle(candidate_tasks)

    scheduled_tasks = candidate_tasks[:TASK_SCHEDULE_LIMIT]
    current_user.scheduled_task_ids = [task.id for task in scheduled_tasks]
    await session.commit()
    return serialize_scheduled_tasks(scheduled_tasks)


async def save_user_progress(
    session: AsyncSession,
    *,
    user: UserRecord,
    task_id: str,
    answer: str,
    comments: list,
    score: float,
    suggestion: str,
    ai_analysis: dict,
) -> None:
    statement = select(UserProgressRecord).where(
        UserProgressRecord.user_id == user.id,
        UserProgressRecord.task_id == task_id,
    )
    progress = (await session.execute(statement)).scalar_one_or_none()

    if progress is None:
        progress = UserProgressRecord(
            user_id=user.id,
            task_id=task_id,
            user_answer=answer,
            user_comments=comments,
            score=score,
            suggestion=suggestion,
            ai_analysis=ai_analysis,
        )
        session.add(progress)
    else:
        progress.user_answer = answer
        progress.user_comments = comments
        progress.score = score
        progress.suggestion = suggestion
        progress.ai_analysis = ai_analysis
        progress.submission_count += 1

    await session.commit()


async def get_current_user(
    request: Request,
    session: SessionDependency,
) -> UserRecord | None:
    user_id = request.session.get("user_id")
    if not user_id:
        return None

    return await session.get(UserRecord, user_id)


CurrentUserDependency = Annotated[UserRecord | None, Depends(get_current_user)]


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/auth/session")
async def get_auth_session(current_user: CurrentUserDependency) -> AuthSession:
    return AuthSession(user=serialize_user(current_user) if current_user else None)


@app.post("/auth/google")
async def login_with_google(
    payload: GoogleLoginRequest,
    request: Request,
    session: SessionDependency,
) -> AuthSession:
    if not GOOGLE_CLIENT_ID:
        raise HTTPException(status_code=503, detail="Google auth is not configured")

    try:
        google_profile = verify_google_credential(payload.credential)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    statement = select(UserRecord).where(UserRecord.google_sub == google_profile["sub"])
    user = (await session.execute(statement)).scalar_one_or_none()

    if user is None:
        user = UserRecord(
            google_sub=google_profile["sub"],
            email=google_profile["email"],
            name=google_profile["name"],
            avatar_url=google_profile["avatar_url"],
            is_admin=is_bootstrap_admin_email(google_profile["email"]),
        )
        session.add(user)
    else:
        user.email = google_profile["email"]
        user.name = google_profile["name"]
        user.avatar_url = google_profile["avatar_url"]

    await session.commit()
    await session.refresh(user)

    request.session["user_id"] = user.id
    return AuthSession(user=serialize_user(user))


@app.post("/auth/logout")
async def logout(request: Request) -> AuthSession:
    request.session.clear()
    return AuthSession(user=None)


@app.get("/me/interests")
async def get_user_interests(
    current_user: CurrentUserDependency,
) -> UserInterestsResponse:
    if current_user is None:
        raise HTTPException(status_code=401, detail="Authentication required")

    return UserInterestsResponse(interests=current_user.user_interests or [])


@app.put("/me/interests")
async def update_user_interests(
    payload: UserInterestsUpdate,
    current_user: CurrentUserDependency,
    session: SessionDependency,
) -> UserInterestsResponse:
    if current_user is None:
        raise HTTPException(status_code=401, detail="Authentication required")

    current_user.user_interests = payload.interests
    await session.commit()

    return UserInterestsResponse(interests=current_user.user_interests)


@app.get("/me/task-schedule")
async def get_task_schedule(
    current_user: CurrentUserDependency,
    task_repository: TaskRepositoryDependency,
    session: SessionDependency,
) -> TaskScheduleResponse:
    if current_user is None:
        raise HTTPException(status_code=401, detail="Authentication required")

    if current_user.scheduled_task_ids:
        scheduled_tasks = await task_repository.list_tasks_by_ids(current_user.scheduled_task_ids)
        return serialize_scheduled_tasks(scheduled_tasks)

    return await generate_and_store_task_schedule(
        current_user=current_user,
        session=session,
        task_repository=task_repository,
    )


@app.post("/me/task-schedule/regenerate")
async def regenerate_task_schedule(
    current_user: CurrentUserDependency,
    task_repository: TaskRepositoryDependency,
    session: SessionDependency,
) -> TaskScheduleResponse:
    if current_user is None:
        raise HTTPException(status_code=401, detail="Authentication required")

    return await generate_and_store_task_schedule(
        current_user=current_user,
        session=session,
        task_repository=task_repository,
    )


@app.get("/me/progress")
async def get_user_progress(
    current_user: CurrentUserDependency,
    session: SessionDependency,
) -> list[UserProgressEntry]:
    if current_user is None:
        raise HTTPException(status_code=401, detail="Authentication required")

    statement = (
        select(UserProgressRecord)
        .options(selectinload(UserProgressRecord.task).selectinload(TaskRecord.reference_issues))
        .where(UserProgressRecord.user_id == current_user.id)
        .order_by(UserProgressRecord.updated_at.desc(), UserProgressRecord.id.desc())
    )
    progress_records = (await session.execute(statement)).scalars().all()

    return [
        UserProgressEntry(
            id=record.id,
            task_id=record.task_id,
            score=record.score,
            suggestion=record.suggestion,
            ai_analysis=record.ai_analysis,
            user_answer=record.user_answer,
            user_comments=record.user_comments,
            submission_count=record.submission_count,
            created_at=record.created_at.isoformat(),
            updated_at=record.updated_at.isoformat(),
            task=UserProgressTaskSummary(
                id=record.task.id,
                title=record.task.title,
                description=record.task.description,
                requirements=record.task.requirements,
                instructions=record.task.instructions,
                language=record.task.language,
                complexity=record.task.complexity,
                submission_mode=record.task.submission_mode,
                code=record.task.code,
                reference_issues=[
                    Issue(
                        id=issue.id,
                        line=issue.line,
                        severity=issue.severity,
                        title=issue.title,
                        description=issue.description,
                        suggestion=issue.suggestion,
                        code=issue.code,
                    )
                    for issue in record.task.reference_issues
                ],
            ),
        )
        for record in progress_records
    ]


@app.get("/me/progress/daily")
async def get_user_progress_daily(
    current_user: CurrentUserDependency,
    session: SessionDependency,
) -> list[UserProgressDailySummary]:
    if current_user is None:
        raise HTTPException(status_code=401, detail="Authentication required")

    statement = (
        select(UserProgressRecord)
        .where(UserProgressRecord.user_id == current_user.id)
        .order_by(UserProgressRecord.updated_at.asc(), UserProgressRecord.id.asc())
    )
    progress_records = (await session.execute(statement)).scalars().all()

    counts_by_day: dict[str, int] = {}
    for record in progress_records:
        day = record.updated_at.date().isoformat()
        counts_by_day[day] = counts_by_day.get(day, 0) + 1

    return [
        UserProgressDailySummary(day=day, completed_tasks=counts_by_day[day])
        for day in sorted(counts_by_day)
    ]


@app.get("/tasks")
async def get_tasks(
    task_repository: TaskRepositoryDependency,
    language: str | None = Query(None),
) -> list:
    filtered = await task_repository.list_tasks(language)
    return [
        {
            "id": task.id,
            "title": task.title,
            "description": task.description,
            "requirements": task.requirements,
            "instructions": task.instructions,
            "language": task.language,
            "complexity": task.complexity,
            "submission_mode": task.submission_mode,
        }
        for task in filtered
    ]


@app.get("/tasks/{task_id}")
async def get_task(
    task_id: str,
    task_repository: TaskRepositoryDependency,
) -> dict:
    task = await task_repository.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    return task.model_dump()


@app.post("/reviews")
async def create_review(
    payload: ReviewCreate,
    task_repository: TaskRepositoryDependency,
) -> dict:
    task = await task_repository.get_task(payload.task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    review = UserReview(
        id=f"review-{uuid4().hex[:8]}",
        task_id=payload.task_id,
        comments=payload.comments,
        answer=payload.answer,
    )
    REVIEWS[review.id] = review
    return review.model_dump()


@app.post("/evaluate")
async def evaluate(
    payload: EvaluationRequest,
    task_repository: TaskRepositoryDependency,
) -> dict:
    review = REVIEWS.get(payload.review_id)
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    task = await task_repository.get_task(review.task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    result = evaluate_review(task, review)

    return {
        "review_id": review.id,
        "task_id": review.task_id,
        "evaluation": result.model_dump(),
    }


@app.post("/ai-analyze")
async def ai_analyze(
    payload: EvaluationRequest,
    task_repository: TaskRepositoryDependency,
    session: SessionDependency,
    current_user: CurrentUserDependency,
) -> dict:
    review = REVIEWS.get(payload.review_id)
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    task = await task_repository.get_task(review.task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    try:
        result = await analyze_review(task, review)
    except Exception as exc:
        error_type = type(exc).__name__
        detail = (
            f"Ollama unavailable: {error_type}" if not str(exc) else f"Ollama unavailable: {exc}"
        )
        raise HTTPException(status_code=502, detail=detail) from exc

    if current_user is not None:
        suggestion_parts = [result.summary, *result.feedback]
        suggestion = "\n".join(part for part in suggestion_parts if part).strip()
        await save_user_progress(
            session,
            user=current_user,
            task_id=review.task_id,
            answer=review.answer,
            comments=[comment.model_dump(mode="json") for comment in review.comments],
            score=result.score,
            suggestion=suggestion,
            ai_analysis=result.model_dump(mode="json"),
        )

    return {
        "review_id": review.id,
        "task_id": review.task_id,
        "analysis": result.model_dump(),
    }
