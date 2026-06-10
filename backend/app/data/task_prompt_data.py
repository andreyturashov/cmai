import json
from pathlib import Path

from app.single_issue_task_prompt import SingleIssueReviewTaskPrompt

_DATA_DIR = Path(__file__).resolve().parent


def load_task_prompts(stem: str) -> list[SingleIssueReviewTaskPrompt]:
    path = _DATA_DIR / f"{stem}.json"
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


EXTRA_PYTHON_TASK_PROMPTS = load_task_prompts("extra_python_task_prompts")
FASTAPI_TASK_PROMPTS = load_task_prompts("fastapi_task_prompts")
DJANGO_TASK_PROMPTS = load_task_prompts("django_task_prompts")
REACT_TASK_PROMPTS = load_task_prompts("react_task_prompts")
MORE_REACT_TASK_PROMPTS = load_task_prompts("more_react_task_prompts")
SECURITY_TASK_PROMPTS = load_task_prompts("security_task_prompts")
TESTING_TASK_PROMPTS = load_task_prompts("testing_task_prompts")
MORE_TESTING_TASK_PROMPTS = load_task_prompts("more_testing_task_prompts")
SYSTEM_DESIGN_TASK_PROMPTS = load_task_prompts("system_design_task_prompts")
MORE_SYSTEM_DESIGN_TASK_PROMPTS = load_task_prompts("more_system_design_task_prompts")
TYPESCRIPT_TASK_PROMPTS = load_task_prompts("typescript_task_prompts")
MORE_TYPESCRIPT_TASK_PROMPTS = load_task_prompts("more_typescript_task_prompts")
DATA_ENGINEERING_TASK_PROMPTS = load_task_prompts("data_engineering_task_prompts")
MORE_DATA_ENGINEERING_TASK_PROMPTS = load_task_prompts("more_data_engineering_task_prompts")
HARD_TESTING_TASK_PROMPTS = load_task_prompts("hard_testing_task_prompts")
HARD_SYSTEM_DESIGN_TASK_PROMPTS = load_task_prompts("hard_system_design_task_prompts")
HARD_TYPESCRIPT_TASK_PROMPTS = load_task_prompts("hard_typescript_task_prompts")
HARD_DATA_ENGINEERING_TASK_PROMPTS = load_task_prompts("hard_data_engineering_task_prompts")
ADDITIONAL_REACT_TASK_PROMPTS = load_task_prompts("additional_react_task_prompts")
SQL_TASK_PROMPTS = load_task_prompts("sql_task_prompts")
HARD_PYTHON_TASK_PROMPTS = load_task_prompts("hard_python_task_prompts")
HARD_DJANGO_TASK_PROMPTS = load_task_prompts("hard_django_task_prompts")
HARD_PYTHON_QUESTION_PROMPTS = load_task_prompts("hard_python_question_prompts")
