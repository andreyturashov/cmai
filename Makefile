SHELL := /bin/zsh

BACKEND_PORT ?= 8000

.PHONY: backend frontend both

backend:
	cd backend && uv run uvicorn app.main:app --reload --port $(BACKEND_PORT)

frontend:
	cd frontend && npm run dev

both:
	$(MAKE) -j2 backend frontend
