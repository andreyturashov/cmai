from pydantic import BaseModel, Field

from .enums import Complexity, Severity


class Issue(BaseModel):
    id: str
    line: int
    severity: Severity
    title: str
    description: str
    suggestion: str
    code: str = ""


class InlineComment(BaseModel):
    line: int
    end_line: int | None = None
    severity: Severity | None = None
    comment: str
    suggestion: str


class Task(BaseModel):
    id: str
    is_completed: bool = False
    title: str
    description: str
    requirements: list[str]
    instructions: list[str]
    language: str
    complexity: Complexity = Complexity.medium
    submission_mode: str = "comments"
    code: str
    reference_issues: list[Issue] = Field(default_factory=list)


class ScheduledTaskEntry(BaseModel):
    id: str
    is_completed: bool
    title: str
    description: str
    requirements: list[str]
    instructions: list[str]
    language: str
    complexity: Complexity = Complexity.medium
    submission_mode: str = "comments"


class TaskScheduleResponse(BaseModel):
    tasks: list[ScheduledTaskEntry] = Field(default_factory=list)


class ReviewCreate(BaseModel):
    task_id: str
    comments: list[InlineComment] = Field(default_factory=list)
    answer: str = ""


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
