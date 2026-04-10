from __future__ import annotations

from typing import Dict
from uuid import uuid4

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.ai_analyzer import analyze_review
from app.evaluator import evaluate_review
from app.models import EvaluationRequest, ReviewCreate, UserReview
from app.seed_data import TASKS

load_dotenv()

app = FastAPI(title="Code Mentor API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

TASKS_BY_ID = {task.id: task for task in TASKS}
REVIEWS: Dict[str, UserReview] = {}


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/tasks")
def get_tasks() -> list:
    return [
        {
            "id": task.id,
            "title": task.title,
            "description": task.description,
            "requirements": task.requirements,
            "instructions": task.instructions,
            "language": task.language,
        }
        for task in TASKS
    ]


@app.get("/tasks/{task_id}")
def get_task(task_id: str) -> dict:
    task = TASKS_BY_ID.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    return task.model_dump()


@app.post("/reviews")
def create_review(payload: ReviewCreate) -> dict:
    if payload.task_id not in TASKS_BY_ID:
        raise HTTPException(status_code=404, detail="Task not found")

    review = UserReview(
        id=f"review-{uuid4().hex[:8]}",
        task_id=payload.task_id,
        comments=payload.comments,
    )
    REVIEWS[review.id] = review
    return review.model_dump()


@app.post("/evaluate")
def evaluate(payload: EvaluationRequest) -> dict:
    review = REVIEWS.get(payload.review_id)
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    task = TASKS_BY_ID[review.task_id]
    result = evaluate_review(task, review)

    return {
        "review_id": review.id,
        "task_id": review.task_id,
        "evaluation": result.model_dump(),
    }


@app.post("/ai-analyze")
async def ai_analyze(payload: EvaluationRequest) -> dict:
    review = REVIEWS.get(payload.review_id)
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    task = TASKS_BY_ID[review.task_id]

    try:
        result = await analyze_review(task, review)
    except Exception as exc:
        error_type = type(exc).__name__
        detail = (
            f"Ollama unavailable: {error_type}"
            if not str(exc)
            else f"Ollama unavailable: {exc}"
        )
        raise HTTPException(status_code=502, detail=detail) from exc

    return {
        "review_id": review.id,
        "task_id": review.task_id,
        "analysis": result.model_dump(),
    }
