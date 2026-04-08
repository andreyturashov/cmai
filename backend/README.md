# Backend

FastAPI service for Code Mentor.

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
