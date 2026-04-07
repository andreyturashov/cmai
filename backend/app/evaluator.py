from __future__ import annotations

from typing import List, Set

from app.models import EvaluationResult, Severity, Task, UserReview


def _similar_comment(comment: str, issue_title: str, issue_description: str) -> bool:
    text = comment.lower()
    haystack = f"{issue_title} {issue_description}".lower()

    keywords = [
        "validate",
        "validation",
        "total",
        "price",
        "error",
        "exception",
        "architecture",
        "service",
        "layer",
        "trust",
    ]

    if any(word in text and word in haystack for word in keywords):
        return True

    overlap = set(text.split()) & set(haystack.split())
    return len(overlap) >= 3


def evaluate_review(task: Task, review: UserReview) -> EvaluationResult:
    matched: Set[str] = set()

    for ref in task.reference_issues:
        for user_comment in review.comments:
            line_close = abs(user_comment.line - ref.line) <= 2
            severity_match = (
                user_comment.severity is not None
                and user_comment.severity == ref.severity
            )
            semantic_match = _similar_comment(
                user_comment.comment, ref.title, ref.description
            )

            if line_close and (severity_match or semantic_match):
                matched.add(ref.id)
                break

    by_severity = {Severity.critical: 0, Severity.medium: 0, Severity.low: 0}
    matched_by_severity = {Severity.critical: 0, Severity.medium: 0, Severity.low: 0}

    for issue in task.reference_issues:
        by_severity[issue.severity] += 1
        if issue.id in matched:
            matched_by_severity[issue.severity] += 1

    total_issues = len(task.reference_issues)
    match_ratio = len(matched) / total_issues if total_issues else 0.0
    score = round(min(10.0, 3 + match_ratio * 7), 1)

    feedback: List[str] = []
    if matched_by_severity[Severity.critical] < by_severity[Severity.critical]:
        feedback.append(
            "Focus on high-impact failures first: validation and money integrity checks."
        )
    if matched_by_severity[Severity.medium] < by_severity[Severity.medium]:
        feedback.append(
            "Look for explicit error handling and API behavior under invalid inputs."
        )
    if matched_by_severity[Severity.low] < by_severity[Severity.low]:
        feedback.append(
            "Call out maintainability and architecture boundaries when visible."
        )
    if not feedback:
        feedback.append(
            "Excellent review coverage. Your issue detection is strong across severities."
        )

    missed = [issue.id for issue in task.reference_issues if issue.id not in matched]

    return EvaluationResult(
        score=score,
        detected_critical=matched_by_severity[Severity.critical],
        total_critical=by_severity[Severity.critical],
        detected_medium=matched_by_severity[Severity.medium],
        total_medium=by_severity[Severity.medium],
        detected_low=matched_by_severity[Severity.low],
        total_low=by_severity[Severity.low],
        matched_issue_ids=sorted(list(matched)),
        missed_issue_ids=missed,
        feedback=feedback,
    )
