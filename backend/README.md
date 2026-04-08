# Backend

FastAPI service for PR Review Trainer MVP.

## Run

```bash
cd backend
uv sync
uv run uvicorn app.main:app --reload --port 8000
```

## Endpoints

- `GET /health`
- `GET /tasks`
- `GET /tasks/{id}`
- `POST /reviews`
- `POST /evaluate`
