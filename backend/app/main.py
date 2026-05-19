from __future__ import annotations

from typing import Annotated
from uuid import uuid4

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.middleware.sessions import SessionMiddleware

from app.admin import setup_admin
from app.ai_analyzer import analyze_review
from app.auth import (
    GOOGLE_CLIENT_ID,
    SESSION_SECRET,
    get_cors_origins,
    verify_google_credential,
)
from app.db import get_session
from app.db_models import UserRecord
from app.evaluator import evaluate_review
from app.models import (
    AuthenticatedUser,
    AuthSession,
    EvaluationRequest,
    GoogleLoginRequest,
    ReviewCreate,
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

    return {
        "review_id": review.id,
        "task_id": review.task_id,
        "analysis": result.model_dump(),
    }
