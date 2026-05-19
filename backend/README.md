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

## Google Auth

Google login is optional. Unauthenticated users can still open the main app and browse tasks.

Set these environment variables to enable sign-in:

```bash
export GOOGLE_CLIENT_ID=<google-oauth-client-id>
export SESSION_SECRET=<long-random-secret>
export CORS_ALLOW_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

Frontend setup:

```bash
export VITE_GOOGLE_CLIENT_ID=<google-oauth-client-id>
```

## Endpoints

- `GET /health`
- `GET /auth/session`
- `POST /auth/google`
- `POST /auth/logout`
- `GET /tasks`
- `GET /tasks/{id}`
- `POST /reviews`
- `POST /evaluate`

## Admin

SQLAdmin is mounted at `GET /admin` for database-backed task management.

Current admin views:

- `tasks`
- `task_issues`
