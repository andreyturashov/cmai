SHELL := /bin/zsh

BACKEND_PORT ?= 8000

.PHONY: backend frontend both frontend-test backend-test migrate backend-seed add-data replace-data backend-db-setup

backend:
	cd backend && uv run uvicorn app.main:app --reload --port $(BACKEND_PORT)

frontend:
	cd frontend && npm run dev

app:
	$(MAKE) -j2 backend frontend

migrate:
	cd backend && uv run alembic upgrade head

backend-seed:
	cd backend && uv run python -m app.data.seed_tasks

add-data:
	cd backend && uv run python -m app.data.seed_tasks

replace-data:
	cd backend && uv run python -m app.data.seed_tasks --replace

test-frontend:
	cd frontend && npm test

test-backend:
	cd backend && uv run pytest

backend-db-setup: backend-migrate backend-seed
