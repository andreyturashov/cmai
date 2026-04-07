from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class Severity(str, Enum):
    critical = "critical"
    medium = "medium"
    low = "low"


class Issue(BaseModel):
    id: str
    line: int
    severity: Severity
    title: str
    description: str
    suggestion: str


class Task(BaseModel):
    id: str
    title: str
    description: str
    requirements: List[str]
    instructions: List[str]
    language: str
    code: str
    reference_issues: List[Issue] = Field(default_factory=list)


class InlineComment(BaseModel):
    line: int
    severity: Optional[Severity] = None
    comment: str
    suggestion: Optional[str] = None


class ReviewCreate(BaseModel):
    task_id: str
    reviewer_name: str = Field(min_length=1, max_length=100)
    comments: List[InlineComment] = Field(default_factory=list)


class UserReview(BaseModel):
    id: str
    task_id: str
    reviewer_name: str
    comments: List[InlineComment]


class EvaluationRequest(BaseModel):
    review_id: str


class EvaluationResult(BaseModel):
    score: float
    detected_critical: int
    total_critical: int
    detected_medium: int
    total_medium: int
    detected_low: int
    total_low: int
    matched_issue_ids: List[str]
    missed_issue_ids: List[str]
    feedback: List[str]
