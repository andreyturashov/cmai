# PR Review Trainer MVP

This project contains both backend and frontend for a PR review training platform.

## Features

- Static PR review task with code snippet
- Inline comment workflow with severity (`critical`, `medium`, `low`)
- Backend evaluation that scores review quality against reference issues
- Two-panel UI (PR context + code review)

## Project Structure

- `backend/` FastAPI API
- `frontend/` React + Vite app

## Run Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

## Run Frontend

```bash
cd frontend
npm install
npm run dev
```

Open the app at `http://localhost:5173`.

## Required API Endpoints

- `GET /tasks`
- `GET /tasks/{id}`
- `POST /reviews`
- `POST /evaluate`

All are implemented in `backend/app/main.py`.
