SHELL := /bin/zsh

BACKEND_PORT ?= 8000

.PHONY: backend frontend both backend-migrate backend-seed backend-db-setup

backend:
	cd backend && uv run uvicorn app.main:app --reload --port $(BACKEND_PORT)

frontend:
	cd frontend && npm run dev

both:
	$(MAKE) -j2 backend frontend

backend-migrate:
	cd backend && uv run alembic upgrade head

backend-seed:
	cd backend && uv run python -m app.seed_tasks

backend-db-setup: backend-migrate backend-seed
