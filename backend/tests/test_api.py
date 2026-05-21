import asyncio
import json
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.ai_analyzer import _build_prompt, analyze_review
from app.db import create_session_factory, get_session
from app.db import normalize_database_url as normalize_db_url
from app.db_models import Base, UserProgressRecord
from app.main import REVIEWS, app
from app.models import AIAnalysisResult, AIIssueVerdict, InlineComment, UserReview
from app.seed_data import TASKS
from app.seed_tasks import replace_seed_tasks

SEED_TASKS_BY_ID = {task.id: task for task in TASKS}


@pytest.fixture()
def client(tmp_path):
    REVIEWS.clear()

    database_path = Path(tmp_path) / "test.db"
    database_url = normalize_db_url(f"sqlite+aiosqlite:///{database_path}")
    engine, session_factory = create_session_factory(database_url)

    async def prepare_database() -> None:
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        await replace_seed_tasks(session_factory, TASKS)

    asyncio.run(prepare_database())

    async def override_get_session():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
    asyncio.run(engine.dispose())


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_admin_home(client):
    resp = client.get("/admin")
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/html")
    assert "Code Mentor Admin" in resp.text


def test_auth_session_defaults_to_anonymous(client):
    resp = client.get("/auth/session")
    assert resp.status_code == 200
    assert resp.json() == {"user": None}


def test_google_login_creates_session(client):
    with (
        patch("app.main.GOOGLE_CLIENT_ID", "test-client-id"),
        patch(
            "app.main.verify_google_credential",
            return_value={
                "sub": "google-user-1",
                "email": "user@example.com",
                "name": "Example User",
                "avatar_url": "https://example.com/avatar.png",
            },
        ),
    ):
        login_resp = client.post("/auth/google", json={"credential": "google-id-token"})

    assert login_resp.status_code == 200
    assert login_resp.json()["user"]["email"] == "user@example.com"

    session_resp = client.get("/auth/session")
    assert session_resp.status_code == 200
    assert session_resp.json()["user"] == {
        "id": 1,
        "email": "user@example.com",
        "name": "Example User",
        "avatar_url": "https://example.com/avatar.png",
    }


def test_google_logout_clears_session(client):
    with (
        patch("app.main.GOOGLE_CLIENT_ID", "test-client-id"),
        patch(
            "app.main.verify_google_credential",
            return_value={
                "sub": "google-user-2",
                "email": "logout@example.com",
                "name": "Logout User",
                "avatar_url": "",
            },
        ),
    ):
        client.post("/auth/google", json={"credential": "google-id-token"})

    logout_resp = client.post("/auth/logout")
    assert logout_resp.status_code == 200
    assert logout_resp.json() == {"user": None}

    session_resp = client.get("/auth/session")
    assert session_resp.status_code == 200
    assert session_resp.json() == {"user": None}


def test_get_user_interests_requires_authentication(client):
    resp = client.get("/me/interests")

    assert resp.status_code == 401
    assert resp.json() == {"detail": "Authentication required"}


def test_update_user_interests_persists_selection(client):
    with (
        patch("app.main.GOOGLE_CLIENT_ID", "test-client-id"),
        patch(
            "app.main.verify_google_credential",
            return_value={
                "sub": "interests-user-1",
                "email": "interests@example.com",
                "name": "Interests User",
                "avatar_url": "",
            },
        ),
    ):
        client.post("/auth/google", json={"credential": "google-id-token"})

    update_resp = client.put(
        "/me/interests",
        json={"interests": ["python_theory", "javascript", "fastapi"]},
    )

    assert update_resp.status_code == 200
    assert update_resp.json() == {"interests": ["python_theory", "javascript", "fastapi"]}

    get_resp = client.get("/me/interests")

    assert get_resp.status_code == 200
    assert get_resp.json() == {"interests": ["python_theory", "javascript", "fastapi"]}


def test_update_user_interests_rejects_more_than_five(client):
    with (
        patch("app.main.GOOGLE_CLIENT_ID", "test-client-id"),
        patch(
            "app.main.verify_google_credential",
            return_value={
                "sub": "interests-user-2",
                "email": "toomany@example.com",
                "name": "Too Many",
                "avatar_url": "",
            },
        ),
    ):
        client.post("/auth/google", json={"credential": "google-id-token"})

    resp = client.put(
        "/me/interests",
        json={
            "interests": [
                "python",
                "python_questions",
                "python_theory",
                "fastapi",
                "django",
                "react",
            ]
        },
    )

    assert resp.status_code == 422


def test_get_task_schedule_requires_authentication(client):
    resp = client.get("/me/task-schedule")

    assert resp.status_code == 401
    assert resp.json() == {"detail": "Authentication required"}


def test_get_task_schedule_uses_interests_and_excludes_completed_tasks(client):
    with (
        patch("app.main.GOOGLE_CLIENT_ID", "test-client-id"),
        patch(
            "app.main.verify_google_credential",
            return_value={
                "sub": "schedule-user-1",
                "email": "schedule@example.com",
                "name": "Schedule User",
                "avatar_url": "",
            },
        ),
    ):
        client.post("/auth/google", json={"credential": "google-id-token"})

    interests_resp = client.put(
        "/me/interests",
        json={"interests": ["python_theory", "javascript"]},
    )
    assert interests_resp.status_code == 200

    review = client.post(
        "/reviews",
        json={
            "task_id": "python-theory-1",
            "comments": [],
            "answer": "Completed once already.",
        },
    ).json()

    mocked_result = AIAnalysisResult(
        all_fixed=True,
        score=8.0,
        detected_critical=0,
        total_critical=0,
        detected_medium=1,
        total_medium=1,
        detected_low=0,
        total_low=0,
        missed_issues=[],
        feedback=["Good enough"],
        issues=[
            AIIssueVerdict(
                issue_id="python-theory-1-i1",
                title="Existing completion",
                severity="medium",
                addressed=True,
                explanation="Already completed.",
            )
        ],
        summary="Stored completion.",
    )

    with patch("app.main.analyze_review", new=AsyncMock(return_value=mocked_result)):
        analyze_resp = client.post("/ai-analyze", json={"review_id": review["id"]})

    assert analyze_resp.status_code == 200

    with patch("app.main.random.shuffle", side_effect=lambda tasks: tasks.reverse()):
        schedule_resp = client.get("/me/task-schedule")

    assert schedule_resp.status_code == 200
    data = schedule_resp.json()
    assert data["tasks"]
    assert len(data["tasks"]) <= 5
    assert all(task["language"] in {"python_theory", "javascript"} for task in data["tasks"])
    assert all(task["id"] != "python-theory-1" for task in data["tasks"])

    second_schedule_resp = client.get("/me/task-schedule")
    assert second_schedule_resp.status_code == 200
    assert second_schedule_resp.json() == data


def test_regenerate_task_schedule_replaces_stored_schedule(client):
    with (
        patch("app.main.GOOGLE_CLIENT_ID", "test-client-id"),
        patch(
            "app.main.verify_google_credential",
            return_value={
                "sub": "schedule-user-2",
                "email": "schedule2@example.com",
                "name": "Schedule User 2",
                "avatar_url": "",
            },
        ),
    ):
        client.post("/auth/google", json={"credential": "google-id-token"})

    interests_resp = client.put(
        "/me/interests",
        json={"interests": ["python_theory", "javascript"]},
    )
    assert interests_resp.status_code == 200

    with patch("app.main.random.shuffle", side_effect=lambda tasks: None):
        initial_resp = client.get("/me/task-schedule")

    assert initial_resp.status_code == 200
    initial_ids = [task["id"] for task in initial_resp.json()["tasks"]]

    with patch("app.main.random.shuffle", side_effect=lambda tasks: tasks.reverse()):
        regenerated_resp = client.post("/me/task-schedule/regenerate")

    assert regenerated_resp.status_code == 200
    regenerated_ids = [task["id"] for task in regenerated_resp.json()["tasks"]]
    assert regenerated_ids
    assert regenerated_ids != initial_ids

    persisted_resp = client.get("/me/task-schedule")
    assert persisted_resp.status_code == 200
    assert [task["id"] for task in persisted_resp.json()["tasks"]] == regenerated_ids


def test_get_user_progress_requires_authentication(client):
    resp = client.get("/me/progress")

    assert resp.status_code == 401
    assert resp.json() == {"detail": "Authentication required"}


def test_get_user_progress_daily_requires_authentication(client):
    resp = client.get("/me/progress/daily")

    assert resp.status_code == 401
    assert resp.json() == {"detail": "Authentication required"}


def test_ai_analyze_stores_user_progress_for_authenticated_user(client):
    with (
        patch("app.main.GOOGLE_CLIENT_ID", "test-client-id"),
        patch(
            "app.main.verify_google_credential",
            return_value={
                "sub": "progress-user-1",
                "email": "progress@example.com",
                "name": "Progress User",
                "avatar_url": "",
            },
        ),
    ):
        client.post("/auth/google", json={"credential": "google-id-token"})

    review = client.post(
        "/reviews",
        json={
            "task_id": "python-theory-1",
            "comments": [
                {
                    "line": 1,
                    "comment": "Explain why the current implementation fails for direct list input.",
                    "suggestion": "Serialize the list before writing.",
                    "severity": "medium",
                }
            ],
            "answer": "Lists are mutable and tuples are immutable.",
        },
    ).json()

    mocked_result = AIAnalysisResult(
        all_fixed=True,
        score=9.5,
        detected_critical=0,
        total_critical=0,
        detected_medium=1,
        total_medium=1,
        detected_low=0,
        total_low=0,
        missed_issues=[],
        feedback=["You explained the tradeoff clearly."],
        issues=[
            AIIssueVerdict(
                issue_id="python-theory-1-i1",
                title="List vs tuple",
                severity="medium",
                addressed=True,
                explanation="You covered the main distinction correctly.",
            )
        ],
        summary="Clear explanation with good terminology.",
    )

    with patch("app.main.analyze_review", new=AsyncMock(return_value=mocked_result)):
        resp = client.post("/ai-analyze", json={"review_id": review["id"]})

    assert resp.status_code == 200

    session_override = app.dependency_overrides[get_session]

    async def fetch_progress_rows() -> list[UserProgressRecord]:
        async for session in session_override():
            result = await session.execute(select(UserProgressRecord))
            return list(result.scalars())
        return []

    progress_rows = asyncio.run(fetch_progress_rows())
    assert len(progress_rows) == 1
    progress = progress_rows[0]
    assert progress.task_id == "python-theory-1"
    assert progress.user_answer == "Lists are mutable and tuples are immutable."
    assert progress.user_comments == [
        {
            "line": 1,
            "end_line": None,
            "severity": "medium",
            "comment": "Explain why the current implementation fails for direct list input.",
            "suggestion": "Serialize the list before writing.",
        }
    ]
    assert progress.score == 9.5
    assert progress.ai_analysis["score"] == 9.5
    assert progress.ai_analysis["summary"] == "Clear explanation with good terminology."
    assert progress.ai_analysis["issues"][0]["issue_id"] == "python-theory-1-i1"
    assert "Clear explanation with good terminology." in progress.suggestion


def test_get_user_progress_returns_saved_progress_with_task_details(client):
    with (
        patch("app.main.GOOGLE_CLIENT_ID", "test-client-id"),
        patch(
            "app.main.verify_google_credential",
            return_value={
                "sub": "progress-user-2",
                "email": "history@example.com",
                "name": "History User",
                "avatar_url": "",
            },
        ),
    ):
        client.post("/auth/google", json={"credential": "google-id-token"})

    review = client.post(
        "/reviews",
        json={
            "task_id": "python-theory-1",
            "comments": [
                {
                    "line": 2,
                    "comment": "This should mention the immutable tuple contract.",
                    "suggestion": "Add an explicit mutability comparison.",
                    "severity": "low",
                }
            ],
            "answer": "Tuples are immutable, lists are mutable.",
        },
    ).json()

    mocked_result = AIAnalysisResult(
        all_fixed=True,
        score=8.5,
        detected_critical=0,
        total_critical=0,
        detected_medium=1,
        total_medium=1,
        detected_low=0,
        total_low=0,
        missed_issues=[],
        feedback=["Good explanation"],
        issues=[
            AIIssueVerdict(
                issue_id="python-theory-1-i1",
                title="List vs tuple",
                severity="medium",
                addressed=True,
                explanation="Correctly identified mutability.",
            )
        ],
        summary="Solid answer.",
    )

    with patch("app.main.analyze_review", new=AsyncMock(return_value=mocked_result)):
        analyze_resp = client.post("/ai-analyze", json={"review_id": review["id"]})

    assert analyze_resp.status_code == 200

    resp = client.get("/me/progress")

    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["task_id"] == "python-theory-1"
    assert data[0]["score"] == 8.5
    assert data[0]["ai_analysis"]["score"] == 8.5
    assert data[0]["ai_analysis"]["summary"] == "Solid answer."
    assert data[0]["ai_analysis"]["issues"][0]["title"] == "List vs tuple"
    assert data[0]["user_answer"] == "Tuples are immutable, lists are mutable."
    assert data[0]["user_comments"] == [
        {
            "line": 2,
            "end_line": None,
            "severity": "low",
            "comment": "This should mention the immutable tuple contract.",
            "suggestion": "Add an explicit mutability comparison.",
        }
    ]
    assert data[0]["task"]["id"] == "python-theory-1"
    assert data[0]["task"]["submission_mode"] == "answer"
    assert data[0]["task"]["reference_issues"]


def test_get_user_progress_daily_returns_counts_grouped_by_day(client):
    with (
        patch("app.main.GOOGLE_CLIENT_ID", "test-client-id"),
        patch(
            "app.main.verify_google_credential",
            return_value={
                "sub": "progress-user-3",
                "email": "calendar@example.com",
                "name": "Calendar User",
                "avatar_url": "",
            },
        ),
    ):
        login_resp = client.post("/auth/google", json={"credential": "google-id-token"})

    assert login_resp.status_code == 200
    user_id = login_resp.json()["user"]["id"]

    session_override = app.dependency_overrides[get_session]

    async def seed_progress_rows() -> None:
        async for session in session_override():
            session.add_all(
                [
                    UserProgressRecord(
                        user_id=user_id,
                        task_id="python-theory-1",
                        score=8.0,
                        suggestion="Solid work.",
                        submission_count=1,
                        updated_at=datetime.fromisoformat("2026-05-19T09:30:00+00:00"),
                    ),
                    UserProgressRecord(
                        user_id=user_id,
                        task_id="python-question-1",
                        score=7.0,
                        suggestion="Good catch.",
                        submission_count=1,
                        updated_at=datetime.fromisoformat("2026-05-19T18:45:00+00:00"),
                    ),
                    UserProgressRecord(
                        user_id=user_id,
                        task_id="pandas-question-1",
                        score=9.0,
                        suggestion="Nice review.",
                        submission_count=1,
                        updated_at=datetime.fromisoformat("2026-05-20T12:15:00+00:00"),
                    ),
                ]
            )
            await session.commit()
            return

    asyncio.run(seed_progress_rows())

    resp = client.get("/me/progress/daily")

    assert resp.status_code == 200
    assert resp.json() == [
        {"day": "2026-05-19", "completed_tasks": 2},
        {"day": "2026-05-20", "completed_tasks": 1},
    ]


def test_ai_analyze_does_not_store_progress_for_anonymous_user(client):
    review = client.post(
        "/reviews",
        json={
            "task_id": "python-theory-1",
            "comments": [],
            "answer": "Lists are mutable and tuples are immutable.",
        },
    ).json()

    mocked_result = AIAnalysisResult(
        all_fixed=True,
        score=9.5,
        detected_critical=0,
        total_critical=0,
        detected_medium=1,
        total_medium=1,
        detected_low=0,
        total_low=0,
        missed_issues=[],
        feedback=["You explained the tradeoff clearly."],
        issues=[
            AIIssueVerdict(
                issue_id="python-theory-1-i1",
                title="List vs tuple",
                severity="medium",
                addressed=True,
                explanation="You covered the main distinction correctly.",
            )
        ],
        summary="Clear explanation with good terminology.",
    )

    with patch("app.main.analyze_review", new=AsyncMock(return_value=mocked_result)):
        resp = client.post("/ai-analyze", json={"review_id": review["id"]})

    assert resp.status_code == 200

    session_override = app.dependency_overrides[get_session]

    async def fetch_progress_count() -> int:
        async for session in session_override():
            result = await session.execute(select(UserProgressRecord))
            return len(list(result.scalars()))
        return 0

    assert asyncio.run(fetch_progress_count()) == 0


# ---------------------------------------------------------------------------
# GET /tasks
# ---------------------------------------------------------------------------


def test_get_tasks_returns_list(client):
    resp = client.get("/tasks")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) == len(TASKS)


def test_get_tasks_has_expected_fields(client):
    resp = client.get("/tasks")
    item = resp.json()[0]
    for key in (
        "id",
        "title",
        "description",
        "requirements",
        "instructions",
        "language",
    ):
        assert key in item
    # code should NOT be in the list endpoint
    assert "code" not in item
    assert "reference_issues" not in item


def test_get_tasks_filter_python(client):
    resp = client.get("/tasks", params={"language": "python"})
    data = resp.json()
    assert len(data) == 44
    assert all(t["language"] == "python" for t in data)


def test_get_tasks_filter_javascript(client):
    resp = client.get("/tasks", params={"language": "javascript"})
    data = resp.json()
    assert len(data) > 0
    assert all(t["language"] == "javascript" for t in data)


def test_get_tasks_filter_python_questions(client):
    resp = client.get("/tasks", params={"language": "python_questions"})
    data = resp.json()
    assert len(data) == 20
    assert all(t["language"] == "python_questions" for t in data)


def test_get_tasks_filter_pandas(client):
    resp = client.get("/tasks", params={"language": "pandas"})
    data = resp.json()
    assert len(data) == 23
    assert all(t["language"] == "pandas" for t in data)


def test_get_tasks_filter_python_theory(client):
    resp = client.get("/tasks", params={"language": "python_theory"})
    data = resp.json()
    assert len(data) == 40
    assert all(t["language"] == "python_theory" for t in data)
    assert all(t["submission_mode"] == "answer" for t in data)


def test_get_tasks_filter_fastapi(client):
    resp = client.get("/tasks", params={"language": "fastapi"})
    data = resp.json()
    assert len(data) == 20
    assert all(t["language"] == "fastapi" for t in data)


def test_get_tasks_filter_django(client):
    resp = client.get("/tasks", params={"language": "django"})
    data = resp.json()
    assert len(data) == 20
    assert all(t["language"] == "django" for t in data)


def test_get_tasks_filter_react(client):
    resp = client.get("/tasks", params={"language": "react"})
    data = resp.json()
    assert len(data) == 20
    assert all(t["language"] == "react" for t in data)


def test_get_tasks_filter_unknown_language(client):
    resp = client.get("/tasks", params={"language": "cobol"})
    assert resp.status_code == 200
    assert resp.json() == []


def test_get_tasks_no_filter_returns_all(client):
    all_resp = client.get("/tasks")
    py_resp = client.get("/tasks", params={"language": "python"})
    py_questions_resp = client.get("/tasks", params={"language": "python_questions"})
    pandas_resp = client.get("/tasks", params={"language": "pandas"})
    py_theory_resp = client.get("/tasks", params={"language": "python_theory"})
    fastapi_resp = client.get("/tasks", params={"language": "fastapi"})
    django_resp = client.get("/tasks", params={"language": "django"})
    react_resp = client.get("/tasks", params={"language": "react"})
    js_resp = client.get("/tasks", params={"language": "javascript"})
    sql_resp = client.get("/tasks", params={"language": "sql"})
    total_filtered = (
        len(py_resp.json())
        + len(py_questions_resp.json())
        + len(pandas_resp.json())
        + len(py_theory_resp.json())
        + len(fastapi_resp.json())
        + len(django_resp.json())
        + len(react_resp.json())
        + len(js_resp.json())
        + len(sql_resp.json())
    )
    assert len(all_resp.json()) == total_filtered


# ---------------------------------------------------------------------------
# GET /tasks/{task_id}
# ---------------------------------------------------------------------------


def test_get_task_by_id(client):
    resp = client.get("/tasks/task-1")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == "task-1"
    assert "code" in data
    assert "reference_issues" in data


def test_get_task_not_found(client):
    resp = client.get("/tasks/nonexistent")
    assert resp.status_code == 404


def test_get_task_has_reference_issues(client):
    resp = client.get("/tasks/task-1")
    issues = resp.json()["reference_issues"]
    assert len(issues) > 0
    for issue in issues:
        assert "id" in issue
        assert "line" in issue
        assert "severity" in issue
        assert "title" in issue


# ---------------------------------------------------------------------------
# POST /reviews
# ---------------------------------------------------------------------------


def test_create_review_empty_comments(client):
    resp = client.post("/reviews", json={"task_id": "task-1", "comments": []})
    assert resp.status_code == 200
    data = resp.json()
    assert data["task_id"] == "task-1"
    assert data["id"].startswith("review-")
    assert data["comments"] == []


def test_create_review_with_comments(client):
    comment = {
        "line": 6,
        "comment": "Missing payload validation",
        "suggestion": "Use Pydantic model",
        "severity": "critical",
    }
    resp = client.post("/reviews", json={"task_id": "task-1", "comments": [comment]})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["comments"]) == 1
    assert data["comments"][0]["line"] == 6


def test_create_review_with_answer(client):
    resp = client.post(
        "/reviews",
        json={
            "task_id": "python-theory-1",
            "comments": [],
            "answer": "Lists are mutable and tuples are immutable.",
        },
    )
    assert resp.status_code == 200
    assert resp.json()["answer"] == "Lists are mutable and tuples are immutable."


def test_create_review_with_line_range(client):
    comment = {
        "line": 6,
        "end_line": 10,
        "comment": "This block has issues",
        "suggestion": "Refactor",
    }
    resp = client.post("/reviews", json={"task_id": "task-1", "comments": [comment]})
    assert resp.status_code == 200
    assert resp.json()["comments"][0]["end_line"] == 10


def test_create_review_invalid_task(client):
    resp = client.post("/reviews", json={"task_id": "nonexistent", "comments": []})
    assert resp.status_code == 404


def test_create_review_missing_task_id(client):
    resp = client.post("/reviews", json={"comments": []})
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# POST /evaluate
# ---------------------------------------------------------------------------


def test_evaluate_no_comments(client):
    review = client.post("/reviews", json={"task_id": "task-1", "comments": []}).json()
    resp = client.post("/evaluate", json={"review_id": review["id"]})
    assert resp.status_code == 200
    data = resp.json()
    assert data["review_id"] == review["id"]
    assert data["task_id"] == "task-1"
    ev = data["evaluation"]
    assert ev["score"] == 3.0
    assert ev["detected_critical"] == 0
    assert ev["total_critical"] > 0


def test_evaluate_with_matching_comment(client):
    comment = {
        "line": 6,
        "comment": "Missing payload validation, no Pydantic model used",
        "suggestion": "Use a Pydantic request model",
        "severity": "critical",
    }
    review = client.post("/reviews", json={"task_id": "task-1", "comments": [comment]}).json()
    resp = client.post("/evaluate", json={"review_id": review["id"]})
    assert resp.status_code == 200
    ev = resp.json()["evaluation"]
    assert ev["detected_critical"] >= 1
    assert ev["score"] > 3.0


def test_evaluate_review_not_found(client):
    resp = client.post("/evaluate", json={"review_id": "nonexistent"})
    assert resp.status_code == 404


def test_evaluate_theory_answer(client):
    review = client.post(
        "/reviews",
        json={
            "task_id": "python-theory-1",
            "comments": [],
            "answer": (
                "Lists are mutable collections that can change over time, while tuples are "
                "immutable and better for fixed values."
            ),
        },
    ).json()
    resp = client.post("/evaluate", json={"review_id": review["id"]})
    ev = resp.json()["evaluation"]
    assert ev["score"] == 10.0
    assert ev["missed_issue_ids"] == []


def test_evaluate_missed_issues_listed(client):
    review = client.post("/reviews", json={"task_id": "task-1", "comments": []}).json()
    resp = client.post("/evaluate", json={"review_id": review["id"]})
    ev = resp.json()["evaluation"]
    assert len(ev["missed_issue_ids"]) == len(SEED_TASKS_BY_ID["task-1"].reference_issues)


def test_evaluate_perfect_review(client):
    """Submit comments that match all reference issues for task-1."""
    task = SEED_TASKS_BY_ID["task-1"]
    comments = [
        {
            "line": issue.line,
            "comment": f"{issue.title} {issue.description}",
            "suggestion": issue.suggestion,
            "severity": issue.severity.value,
        }
        for issue in task.reference_issues
    ]
    review = client.post("/reviews", json={"task_id": "task-1", "comments": comments}).json()
    resp = client.post("/evaluate", json={"review_id": review["id"]})
    ev = resp.json()["evaluation"]
    assert ev["score"] == 10.0
    assert ev["missed_issue_ids"] == []


# ---------------------------------------------------------------------------
# Seed data integrity
# ---------------------------------------------------------------------------


def test_all_tasks_have_unique_ids():
    ids = [t.id for t in TASKS]
    assert len(ids) == len(set(ids))


def test_all_tasks_have_reference_issues():
    for task in TASKS:
        assert len(task.reference_issues) >= 1, f"Task {task.id} has no issues"


def test_all_tasks_have_valid_language():
    valid = {
        "python",
        "python_questions",
        "pandas",
        "python_theory",
        "fastapi",
        "django",
        "react",
        "javascript",
        "sql",
    }
    for task in TASKS:
        assert task.language in valid, f"Task {task.id} has invalid language: {task.language}"


def test_theory_tasks_use_answer_submission_mode():
    for task in TASKS:
        if task.language == "python_theory":
            assert task.submission_mode == "answer"


def test_all_issues_have_valid_severity():
    for task in TASKS:
        for issue in task.reference_issues:
            assert issue.severity in (
                "critical",
                "medium",
                "low",
            ), f"Issue {issue.id} in task {task.id} has invalid severity"


def test_all_issue_ids_unique_within_task():
    for task in TASKS:
        ids = [i.id for i in task.reference_issues]
        assert len(ids) == len(set(ids)), f"Duplicate issue IDs in task {task.id}"


def test_each_language_has_tasks():
    languages = {t.language for t in TASKS}
    assert "python" in languages
    assert "fastapi" in languages
    assert "django" in languages
    assert "react" in languages
    assert "javascript" in languages
    assert "python_questions" in languages
    assert "pandas" in languages
    assert "python_theory" in languages
    assert "sql" in languages


# ---------------------------------------------------------------------------
# AI Analyzer – unit tests (mocked Ollama)
# ---------------------------------------------------------------------------

TASK_1 = SEED_TASKS_BY_ID["task-1"]


def _make_review(task_id="task-1", comments=None):
    return UserReview(
        id="review-test",
        task_id=task_id,
        comments=comments or [],
    )


def _ollama_json_response(data: dict):
    """Create a mock httpx.Response with Ollama JSON payload."""
    import httpx

    return httpx.Response(
        status_code=200,
        json={"response": json.dumps(data)},
        request=httpx.Request("POST", "http://localhost/api/generate"),
    )


def _build_ollama_result(task, addressed_ids=None, score=None):
    """Build a valid Ollama-style JSON result for a task."""
    addressed_ids = addressed_ids or set()
    issues = []
    for issue in task.reference_issues:
        issues.append(
            {
                "issue_id": issue.id,
                "title": issue.title,
                "severity": issue.severity.value,
                "addressed": issue.id in addressed_ids,
                "explanation": "Test explanation",
            }
        )
    all_fixed = all(i["addressed"] for i in issues)
    return {
        "all_fixed": all_fixed,
        "score": score if score is not None else (10.0 if all_fixed else 3.0),
        "issues": issues,
        "summary": "Test summary",
    }


def test_build_prompt_with_comments():
    review = _make_review(
        comments=[
            InlineComment(line=6, comment="Bad validation", suggestion="Fix it"),
        ]
    )
    prompt = _build_prompt(TASK_1, review)
    assert "Bad validation" in prompt
    assert "Fix it" in prompt
    assert "Known issues" in prompt


def test_build_prompt_no_comments():
    review = _make_review()
    prompt = _build_prompt(TASK_1, review)
    assert "(no comments submitted)" in prompt


def test_build_prompt_with_line_range():
    review = _make_review(
        comments=[
            InlineComment(line=6, end_line=10, comment="Range comment", suggestion="Fix"),
        ]
    )
    prompt = _build_prompt(TASK_1, review)
    assert "Line 6-10" in prompt


def test_build_prompt_for_theory_answer_prevents_rubric_splitting():
    task = SEED_TASKS_BY_ID["python-theory-7"]
    review = UserReview(
        id="review-theory",
        task_id=task.id,
        comments=[],
        answer="Uses with for cleanup.",
    )

    prompt = _build_prompt(task, review)

    assert "Return exactly 1 item(s) in the issues array." in prompt
    assert "Do not split one rubric entry into multiple sub-issues." in prompt
    assert (
        "If the answer explains the same idea in different words, count that as covered." in prompt
    )


@pytest.mark.anyio
async def test_analyze_review_all_addressed():
    review = _make_review()
    all_ids = {i.id for i in TASK_1.reference_issues}
    data = _build_ollama_result(TASK_1, addressed_ids=all_ids, score=10.0)

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.post = AsyncMock(return_value=_ollama_json_response(data))

    with patch("app.ai_analyzer.httpx.AsyncClient", return_value=mock_client):
        result = await analyze_review(TASK_1, review)

    assert result.all_fixed is True
    assert result.score == 10.0
    assert result.missed_issues == []
    assert len(result.issues) == len(TASK_1.reference_issues)


@pytest.mark.anyio
async def test_analyze_review_none_addressed():
    review = _make_review()
    data = _build_ollama_result(TASK_1, addressed_ids=set(), score=0.0)

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.post = AsyncMock(return_value=_ollama_json_response(data))

    with patch("app.ai_analyzer.httpx.AsyncClient", return_value=mock_client):
        result = await analyze_review(TASK_1, review)

    assert result.all_fixed is False
    assert result.score == 0.0
    assert len(result.missed_issues) == len(TASK_1.reference_issues)


@pytest.mark.anyio
async def test_analyze_review_partial():
    review = _make_review()
    first_id = TASK_1.reference_issues[0].id
    data = _build_ollama_result(TASK_1, addressed_ids={first_id}, score=5.0)

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.post = AsyncMock(return_value=_ollama_json_response(data))

    with patch("app.ai_analyzer.httpx.AsyncClient", return_value=mock_client):
        result = await analyze_review(TASK_1, review)

    assert result.all_fixed is False
    assert result.detected_critical >= 1
    assert len(result.missed_issues) == len(TASK_1.reference_issues) - 1


@pytest.mark.anyio
async def test_analyze_review_invalid_json_response():
    import httpx as httpx_mod

    review = _make_review()

    mock_resp = httpx_mod.Response(
        status_code=200,
        json={"response": "not valid json {{{"},
        request=httpx_mod.Request("POST", "http://localhost/api/generate"),
    )

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.post = AsyncMock(return_value=mock_resp)

    with patch("app.ai_analyzer.httpx.AsyncClient", return_value=mock_client):
        result = await analyze_review(TASK_1, review)

    assert result.all_fixed is False
    assert result.score == 3.0
    assert "could not parse" in result.summary.lower()


@pytest.mark.anyio
async def test_analyze_review_markdown_fenced_response():
    import httpx as httpx_mod

    review = _make_review()
    data = _build_ollama_result(TASK_1, addressed_ids=set(), score=2.0)
    fenced = f"```json\n{json.dumps(data)}\n```"

    mock_resp = httpx_mod.Response(
        status_code=200,
        json={"response": fenced},
        request=httpx_mod.Request("POST", "http://localhost/api/generate"),
    )

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.post = AsyncMock(return_value=mock_resp)

    with patch("app.ai_analyzer.httpx.AsyncClient", return_value=mock_client):
        result = await analyze_review(TASK_1, review)

    assert result.score == 2.0
    assert result.summary == "Test summary"


@pytest.mark.anyio
async def test_analyze_review_no_score_computes_from_verdicts():
    review = _make_review()
    data = _build_ollama_result(TASK_1, addressed_ids=set())
    del data["score"]

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.post = AsyncMock(return_value=_ollama_json_response(data))

    with patch("app.ai_analyzer.httpx.AsyncClient", return_value=mock_client):
        result = await analyze_review(TASK_1, review)

    assert result.score == 0.0


@pytest.mark.anyio
async def test_analyze_review_no_score_with_addressed_issues():
    """When AI omits score, it should be computed from addressed reference issues."""
    review = _make_review()
    all_ids = {i.id for i in TASK_1.reference_issues}
    data = _build_ollama_result(TASK_1, addressed_ids=all_ids)
    del data["score"]

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.post = AsyncMock(return_value=_ollama_json_response(data))

    with patch("app.ai_analyzer.httpx.AsyncClient", return_value=mock_client):
        result = await analyze_review(TASK_1, review)

    assert result.score == 10.0


@pytest.mark.anyio
async def test_analyze_review_invalid_score_type():
    review = _make_review()
    data = _build_ollama_result(TASK_1, addressed_ids=set())
    data["score"] = "not a number"

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.post = AsyncMock(return_value=_ollama_json_response(data))

    with patch("app.ai_analyzer.httpx.AsyncClient", return_value=mock_client):
        result = await analyze_review(TASK_1, review)

    assert result.score == 0.0


@pytest.mark.anyio
async def test_analyze_review_unknown_issue_id_in_response():
    review = _make_review()
    data = _build_ollama_result(TASK_1, addressed_ids=set())
    data["issues"].append(
        {
            "issue_id": "unknown-999",
            "title": "Made up issue",
            "severity": "low",
            "addressed": True,
            "explanation": "Phantom issue",
        }
    )

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.post = AsyncMock(return_value=_ollama_json_response(data))

    with patch("app.ai_analyzer.httpx.AsyncClient", return_value=mock_client):
        result = await analyze_review(TASK_1, review)

    # Unknown issues should be ignored and only known rubric items should be returned.
    verdict_ids = {v.issue_id for v in result.issues}
    assert "unknown-999" not in verdict_ids
    assert verdict_ids == {issue.id for issue in TASK_1.reference_issues}


@pytest.mark.anyio
async def test_analyze_review_deduplicates_theory_issue_verdicts():
    import httpx as httpx_mod

    task = SEED_TASKS_BY_ID["python-theory-7"]
    review = UserReview(
        id="review-theory",
        task_id=task.id,
        comments=[],
        answer="Context managers use with to clean up resources and can define enter and exit methods.",
    )
    duplicated = {
        "all_fixed": False,
        "score": 6.0,
        "issues": [
            {
                "issue_id": task.reference_issues[0].id,
                "title": task.reference_issues[0].title,
                "severity": task.reference_issues[0].severity.value,
                "addressed": True,
                "explanation": "First verdict",
            },
            {
                "issue_id": task.reference_issues[0].id,
                "title": task.reference_issues[0].title,
                "severity": task.reference_issues[0].severity.value,
                "addressed": False,
                "explanation": "Duplicate verdict",
            },
            {
                "issue_id": "hallucinated-1",
                "title": task.reference_issues[0].title,
                "severity": "medium",
                "addressed": False,
                "explanation": "Hallucinated verdict",
            },
        ],
        "summary": "Partial coverage",
    }

    mock_resp = httpx_mod.Response(
        status_code=200,
        json={"response": json.dumps(duplicated)},
        request=httpx_mod.Request("POST", "http://localhost/api/generate"),
    )

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.post = AsyncMock(return_value=mock_resp)

    with patch("app.ai_analyzer.httpx.AsyncClient", return_value=mock_client):
        result = await analyze_review(task, review)

    assert len(result.issues) == 1
    assert result.issues[0].issue_id == task.reference_issues[0].id
    assert result.issues[0].addressed is True
    assert result.issues[0].explanation == "First verdict"
    assert result.score == 10.0
    assert result.all_fixed is True


@pytest.mark.anyio
async def test_analyze_review_theory_uses_normalized_score_over_ai_score():
    import httpx as httpx_mod

    task = SEED_TASKS_BY_ID["python-theory-9"]
    review = UserReview(
        id="review-theory-2",
        task_id=task.id,
        comments=[],
        answer="Else runs only when no exception happens, and finally always runs for cleanup.",
    )
    contradictory = {
        "all_fixed": False,
        "score": 6.0,
        "issues": [
            {
                "issue_id": task.reference_issues[0].id,
                "title": task.reference_issues[0].title,
                "severity": task.reference_issues[0].severity.value,
                "addressed": True,
                "explanation": "You covered the expected concept clearly.",
            }
        ],
        "summary": "Strong answer.",
    }

    mock_resp = httpx_mod.Response(
        status_code=200,
        json={"response": json.dumps(contradictory)},
        request=httpx_mod.Request("POST", "http://localhost/api/generate"),
    )

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.post = AsyncMock(return_value=mock_resp)

    with patch("app.ai_analyzer.httpx.AsyncClient", return_value=mock_client):
        result = await analyze_review(task, review)

    assert result.score == 10.0
    assert result.all_fixed is True
    assert result.issues[0].addressed is True


# ---------------------------------------------------------------------------
# POST /ai-analyze endpoint (mocked Ollama)
# ---------------------------------------------------------------------------


def test_ai_analyze_success(client):
    import httpx as httpx_mod

    review = client.post("/reviews", json={"task_id": "task-1", "comments": []}).json()
    data = _build_ollama_result(TASK_1, addressed_ids=set(), score=3.0)

    mock_resp = httpx_mod.Response(
        status_code=200,
        json={"response": json.dumps(data)},
        request=httpx_mod.Request("POST", "http://localhost/api/generate"),
    )

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.post = AsyncMock(return_value=mock_resp)

    with patch("app.ai_analyzer.httpx.AsyncClient", return_value=mock_client):
        resp = client.post("/ai-analyze", json={"review_id": review["id"]})

    assert resp.status_code == 200
    body = resp.json()
    assert body["review_id"] == review["id"]
    assert body["task_id"] == "task-1"
    assert "analysis" in body
    assert body["analysis"]["score"] == 3.0


def test_ai_analyze_review_not_found(client):
    resp = client.post("/ai-analyze", json={"review_id": "nonexistent"})
    assert resp.status_code == 404


def test_ai_analyze_ollama_unavailable(client):
    review = client.post("/reviews", json={"task_id": "task-1", "comments": []}).json()

    with patch("app.ai_analyzer.httpx.AsyncClient", side_effect=ConnectionError("refused")):
        resp = client.post("/ai-analyze", json={"review_id": review["id"]})

    assert resp.status_code == 502
    assert "unavailable" in resp.json()["detail"].lower()
