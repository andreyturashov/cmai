from enum import Enum

ALLOWED_INTERESTS = {
    "python",
    "python_questions",
    "asyncio",
    "graphql",
    "security",
    "testing",
    "system_design",
    "typescript",
    "data_engineering",
    "pandas",
    "langchain_langgraph",
    "machine_learning",
    "python_theory",
    "fastapi",
    "django",
    "react",
    "javascript",
    "sql",
}


class Severity(str, Enum):
    critical = "critical"
    medium = "medium"
    low = "low"


class Complexity(str, Enum):
    easy = "easy"
    medium = "medium"
    hard = "hard"
