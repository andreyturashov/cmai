# Backend

FastAPI service for Code Mentor.

## Run

```bash
cd backend
uv sync
uv run alembic upgrade head
uv run python -m app.seed_tasks
uv run uvicorn app.main:app --reload --port 8000
```

## Database

The backend now loads tasks from Postgres using async SQLAlchemy.

Set `DATABASE_URL` before running the API or migrations. Example local default:

```bash
export DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/codementorai
```

Useful commands:

```bash
uv run alembic upgrade head
uv run python -m app.seed_tasks
```

## Endpoints

- `GET /health`
- `GET /tasks`
- `GET /tasks/{id}`
- `POST /reviews`
- `POST /evaluate`
