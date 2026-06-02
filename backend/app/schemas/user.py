from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, Field, field_validator

from .enums import ALLOWED_INTERESTS, Complexity

if TYPE_CHECKING:
    from .task import AIAnalysisResult, InlineComment, Issue
else:
    from .task import AIAnalysisResult, InlineComment, Issue


class GoogleLoginRequest(BaseModel):
    credential: str


class AuthenticatedUser(BaseModel):
    id: int
    email: str
    name: str
    avatar_url: str = ""


class AuthSession(BaseModel):
    user: AuthenticatedUser | None = None


class UserInterestsResponse(BaseModel):
    interests: list[str] = Field(default_factory=list)


class UserInterestsUpdate(BaseModel):
    interests: list[str] = Field(default_factory=list, max_length=5)

    @field_validator("interests")
    @classmethod
    def validate_interests(cls, interests: list[str]) -> list[str]:
        if len(interests) != len(set(interests)):
            raise ValueError("Interests must be unique")

        invalid = [interest for interest in interests if interest not in ALLOWED_INTERESTS]
        if invalid:
            raise ValueError(f"Unsupported interests: {', '.join(invalid)}")

        return interests


class UserProgressTaskSummary(BaseModel):
    id: str
    title: str
    description: str
    requirements: list[str]
    instructions: list[str]
    language: str
    complexity: Complexity = Complexity.medium
    submission_mode: str = "comments"
    code: str
    reference_issues: list[Issue] = Field(default_factory=list)


# Rebuild models after forward references are resolved
UserProgressTaskSummary.model_rebuild()


class UserProgressEntry(BaseModel):
    id: int
    task_id: str
    score: float
    suggestion: str
    ai_analysis: AIAnalysisResult | None = None
    user_answer: str
    user_comments: list[InlineComment] = Field(default_factory=list)
    submission_count: int
    created_at: str
    updated_at: str
    task: UserProgressTaskSummary


class UserProgressDailySummary(BaseModel):
    day: str
    completed_tasks: int
