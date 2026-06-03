from typing import Literal, TypedDict


class SingleIssueReviewTaskPrompt(TypedDict):
    title: str
    description: str
    code: str
    issue_line: int
    issue_severity: Literal["critical", "medium", "low"]
    issue_title: str
    issue_description: str
    issue_suggestion: str
    issue_code: str
