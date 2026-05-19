from __future__ import annotations

from enum import Enum

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
    code: str = ""


class Task(BaseModel):
    id: str
    title: str
    description: str
    requirements: list[str]
    instructions: list[str]
    language: str
    submission_mode: str = "comments"
    code: str
    reference_issues: list[Issue] = Field(default_factory=list)


class InlineComment(BaseModel):
    line: int
    end_line: int | None = None
    severity: Severity | None = None
    comment: str
    suggestion: str


class ReviewCreate(BaseModel):
    task_id: str
    comments: list[InlineComment] = Field(default_factory=list)
    answer: str = ""


class GoogleLoginRequest(BaseModel):
    credential: str


class AuthenticatedUser(BaseModel):
    id: int
    email: str
    name: str
    avatar_url: str = ""


class AuthSession(BaseModel):
    user: AuthenticatedUser | None = None


class UserReview(BaseModel):
    id: str
    task_id: str
    comments: list[InlineComment]
    answer: str = ""


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
    matched_issue_ids: list[str]
    missed_issue_ids: list[str]
    feedback: list[str]


class AIIssueVerdict(BaseModel):
    issue_id: str
    title: str = ""
    severity: str = ""
    addressed: bool
    explanation: str


class AIAnalysisResult(BaseModel):
    all_fixed: bool
    score: float
    detected_critical: int
    total_critical: int
    detected_medium: int
    total_medium: int
    detected_low: int
    total_low: int
    missed_issues: list[str]
    feedback: list[str]
    issues: list[AIIssueVerdict]
    summary: str
