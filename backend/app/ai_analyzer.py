from __future__ import annotations

import json
import logging
import os

import httpx

from app.models import AIAnalysisResult, AIIssueVerdict, Severity, Task, UserReview

logger = logging.getLogger(__name__)

OLLAMA_BASE = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1")


def _build_prompt(task: Task, review: UserReview) -> str:
    code_lines = task.code.split("\n")
    numbered = "\n".join(f"{i + 1}: {line}" for i, line in enumerate(code_lines))

    issues_block = "\n".join(
        f"- [{issue.id}] Line {issue.line} ({issue.severity.value}): "
        f"{issue.title} — {issue.description}"
        for issue in task.reference_issues
    )

    comments_block = (
        "\n".join(
            f"- Line {c.line}{f'-{c.end_line}' if c.end_line else ''}: "
            f"{c.comment} | Suggestion: {c.suggestion}"
            for c in review.comments
        )
        or "(no comments submitted)"
    )

    answer_block = review.answer.strip() or "(no answer submitted)"
    issue_count = len(task.reference_issues)

    if task.submission_mode == "answer":
        return f"""You are a strict Python theory mentor. Your job is to evaluate whether a student's free-text answer correctly covers the expected concepts for a theory question.

IMPORTANT: Write all explanations addressing the user directly using \"you/your\" (second person). Never say \"the student\" or \"they\".

## Question shown to the student
```python
{numbered}
```

## Expected concepts / rubric
{issues_block}

## Student answer
{answer_block}

## Evaluation rules
Evaluate the rubric holistically, but return verdicts only for the rubric entries listed above:
1. Match on meaning, not exact wording.
2. If the answer explains the same idea in different words, count that as covered.
3. If one sentence implies a rubric point and a nearby example or follow-up sentence makes it clear, count the point as covered.
4. Do not require the answer to repeat rubric keywords verbatim or in the same order.
5. A vague answer does not count.
6. If no answer was submitted, nothing is addressed and score = 0.

## Output constraints
- Return exactly {issue_count} item(s) in the issues array.
- Reuse the exact issue_id values from the rubric above.
- Do not invent extra issues.
- Do not split one rubric entry into multiple sub-issues.
- If an answer is partially correct, keep the single rubric entry and explain which parts you think are still missing.

## Scoring guide
- Score = (addressed concepts / total concepts) * 10, rounded to 1 decimal
- If the answer is empty, score = 0

Return ONLY valid JSON (no markdown fences, no extra text) with this exact schema:
{{
    \"all_fixed\": <bool — true only if EVERY expected concept is covered>,
    \"score\": <number 0-10>,
    \"issues\": [
        {{
            \"issue_id\": \"<id from rubric>\",
            \"title\": \"<title from rubric>\",
            \"severity\": \"<critical|medium|low>\",
            \"addressed\": <bool>,
            \"explanation\": \"<1-2 sentences using 'you/your': whether your answer covers this concept and why. Start with the concept title.>\"
        }}
    ],
    \"summary\": \"<one sentence overall assessment>\"
}}
"""

    return f"""You are a strict code-review mentor. Your job is to evaluate whether a student's review comments correctly identify known issues in a code snippet.

Be strict: a comment only "addresses" an issue if it clearly describes the SAME problem (not just nearby code). Vague or tangential comments do NOT count.

IMPORTANT: Write all explanations addressing the user directly using "you/your" (second person). Never say "the student" or "they" — always say "you".

## Code
```
{numbered}
```

## Known issues (the student should find these)
{issues_block}

## Student's review comments
{comments_block}

## Evaluation rules
For EACH known issue, decide whether any student comment addresses it:
1. The comment must describe the SAME vulnerability, bug, or concern (semantic match — exact wording not required).
2. The comment must target approximately the same code region (within ±3 lines).
3. A comment about a DIFFERENT problem on the same line does NOT count.
4. If no comments were submitted, nothing is addressed.

## Scoring guide
- critical issues are worth 3 points each
- medium issues are worth 2 points each
- low issues are worth 1 point each
- Score = (addressed points / total points) * 10, rounded to 1 decimal
- If no comments submitted, score = 0

Return ONLY valid JSON (no markdown fences, no extra text) with this exact schema:
{{
  "all_fixed": <bool — true only if EVERY issue is addressed>,
  "score": <number 0-10>,
  "issues": [
    {{
      "issue_id": "<id from known issues>",
      "title": "<title from known issues>",
      "severity": "<critical|medium|low>",
      "addressed": <bool>,
      "explanation": "<1-2 sentences using 'you/your': which of your comments matches (or why none of your comments do). Start with the issue title.>"
    }}
  ],
  "summary": "<one sentence overall assessment>"
}}
"""


async def analyze_review(task: Task, review: UserReview) -> AIAnalysisResult:
    prompt = _build_prompt(task, review)

    async with httpx.AsyncClient(timeout=300.0) as client:
        resp = await client.post(
            f"{OLLAMA_BASE}/api/generate",
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.1},
            },
        )
        resp.raise_for_status()

    raw = resp.json().get("response", "")
    logger.debug("Ollama raw response: %s", raw)

    # Strip markdown fences if model adds them despite instructions
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[1] if "\n" in cleaned else cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    cleaned = cleaned.strip()

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        logger.warning("Failed to parse AI response as JSON: %s", cleaned[:300])
        total_by = {Severity.critical: 0, Severity.medium: 0, Severity.low: 0}
        for issue in task.reference_issues:
            total_by[issue.severity] += 1
        return AIAnalysisResult(
            all_fixed=False,
            score=3.0,
            detected_critical=0,
            total_critical=total_by[Severity.critical],
            detected_medium=0,
            total_medium=total_by[Severity.medium],
            detected_low=0,
            total_low=total_by[Severity.low],
            missed_issues=[i.title for i in task.reference_issues],
            feedback=["AI analysis could not parse the response. Please try again."],
            issues=[],
            summary="AI analysis could not parse the response.",
        )

    ref_by_id = {issue.id: issue for issue in task.reference_issues}
    raw_items = data.get("issues", [])
    normalized_by_id: dict[str, dict] = {}
    for item in raw_items:
        iid = item.get("issue_id", "")
        if iid not in ref_by_id or iid in normalized_by_id:
            continue
        normalized_by_id[iid] = item

    verdicts = []
    for issue in task.reference_issues:
        item = normalized_by_id.get(issue.id, {})
        verdicts.append(
            AIIssueVerdict(
                issue_id=issue.id,
                title=issue.title,
                severity=issue.severity.value,
                addressed=bool(item.get("addressed", False)),
                explanation=item.get("explanation", ""),
            )
        )

    addressed_ids = {v.issue_id for v in verdicts if v.addressed}
    by_sev = {Severity.critical: 0, Severity.medium: 0, Severity.low: 0}
    det_sev = {Severity.critical: 0, Severity.medium: 0, Severity.low: 0}
    missed: list[str] = []

    for issue in task.reference_issues:
        by_sev[issue.severity] += 1
        if issue.id in addressed_ids:
            det_sev[issue.severity] += 1
        else:
            missed.append(issue.title)

    total_points = 0
    addressed_points = 0
    weight = {Severity.critical: 3, Severity.medium: 2, Severity.low: 1}
    for issue in task.reference_issues:
        w = weight[issue.severity]
        total_points += w
        if issue.id in addressed_ids:
            addressed_points += w

    computed_score = round((addressed_points / total_points) * 10, 1) if total_points else 0.0
    normalized_all_fixed = len(addressed_ids) == len(task.reference_issues)

    # In answer mode, prefer the normalized verdict-derived score to avoid
    # contradictory AI outputs like addressed=true with score < 10.
    if task.submission_mode == "answer":
        score = computed_score
    else:
        ai_score = data.get("score")
        if ai_score is not None:
            try:
                score = round(min(10.0, max(0.0, float(ai_score))), 1)
            except (TypeError, ValueError):
                score = 0.0
        else:
            score = computed_score

    feedback: list[str] = []
    if task.submission_mode == "answer":
        if not review.answer.strip():
            feedback.append("Add an answer before submitting so your correctness can be analyzed.")
        elif len(addressed_ids) < len(task.reference_issues):
            feedback.append(
                "Your answer is close, but it should cover more of the expected concepts."
            )
        else:
            feedback.append("Strong answer — you covered the expected concepts.")
    else:
        if det_sev[Severity.critical] < by_sev[Severity.critical]:
            feedback.append("Focus on high-impact failures first: validation and security checks.")
        if det_sev[Severity.medium] < by_sev[Severity.medium]:
            feedback.append("Look for explicit error handling and edge-case behavior.")
        if det_sev[Severity.low] < by_sev[Severity.low]:
            feedback.append("Consider maintainability and architecture improvements.")
        if not feedback:
            feedback.append("Excellent review — all issues identified.")

    return AIAnalysisResult(
        all_fixed=normalized_all_fixed,
        score=score,
        detected_critical=det_sev[Severity.critical],
        total_critical=by_sev[Severity.critical],
        detected_medium=det_sev[Severity.medium],
        total_medium=by_sev[Severity.medium],
        detected_low=det_sev[Severity.low],
        total_low=by_sev[Severity.low],
        missed_issues=missed,
        feedback=feedback,
        issues=verdicts,
        summary=data.get("summary", ""),
    )
