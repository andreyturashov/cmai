import pytest
from fastapi.testclient import TestClient

from app.main import REVIEWS, TASKS_BY_ID, app
from app.seed_data import TASKS


@pytest.fixture()
def client():
    REVIEWS.clear()
    return TestClient(app)


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


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
    assert len(data) > 0
    assert all(t["language"] == "python" for t in data)


def test_get_tasks_filter_javascript(client):
    resp = client.get("/tasks", params={"language": "javascript"})
    data = resp.json()
    assert len(data) > 0
    assert all(t["language"] == "javascript" for t in data)


def test_get_tasks_filter_go(client):
    resp = client.get("/tasks", params={"language": "go"})
    data = resp.json()
    assert len(data) > 0
    assert all(t["language"] == "go" for t in data)


def test_get_tasks_filter_rust(client):
    resp = client.get("/tasks", params={"language": "rust"})
    data = resp.json()
    assert len(data) > 0
    assert all(t["language"] == "rust" for t in data)


def test_get_tasks_filter_unknown_language(client):
    resp = client.get("/tasks", params={"language": "cobol"})
    assert resp.status_code == 200
    assert resp.json() == []


def test_get_tasks_no_filter_returns_all(client):
    all_resp = client.get("/tasks")
    py_resp = client.get("/tasks", params={"language": "python"})
    js_resp = client.get("/tasks", params={"language": "javascript"})
    go_resp = client.get("/tasks", params={"language": "go"})
    rust_resp = client.get("/tasks", params={"language": "rust"})
    total_filtered = (
        len(py_resp.json())
        + len(js_resp.json())
        + len(go_resp.json())
        + len(rust_resp.json())
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
    review = client.post(
        "/reviews", json={"task_id": "task-1", "comments": [comment]}
    ).json()
    resp = client.post("/evaluate", json={"review_id": review["id"]})
    assert resp.status_code == 200
    ev = resp.json()["evaluation"]
    assert ev["detected_critical"] >= 1
    assert ev["score"] > 3.0


def test_evaluate_review_not_found(client):
    resp = client.post("/evaluate", json={"review_id": "nonexistent"})
    assert resp.status_code == 404


def test_evaluate_missed_issues_listed(client):
    review = client.post("/reviews", json={"task_id": "task-1", "comments": []}).json()
    resp = client.post("/evaluate", json={"review_id": review["id"]})
    ev = resp.json()["evaluation"]
    assert len(ev["missed_issue_ids"]) == len(TASKS_BY_ID["task-1"].reference_issues)


def test_evaluate_perfect_review(client):
    """Submit comments that match all reference issues for task-1."""
    task = TASKS_BY_ID["task-1"]
    comments = [
        {
            "line": issue.line,
            "comment": f"{issue.title} {issue.description}",
            "suggestion": issue.suggestion,
            "severity": issue.severity.value,
        }
        for issue in task.reference_issues
    ]
    review = client.post(
        "/reviews", json={"task_id": "task-1", "comments": comments}
    ).json()
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
    valid = {"python", "javascript", "go", "rust"}
    for task in TASKS:
        assert (
            task.language in valid
        ), f"Task {task.id} has invalid language: {task.language}"


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
    assert "javascript" in languages
    assert "go" in languages
    assert "rust" in languages
