SHELL := /bin/zsh

PROJECT_VENV_PYTHON := $(abspath .venv/bin/python)

ifneq ("$(wildcard $(PROJECT_VENV_PYTHON))","")
PYTHON ?= $(PROJECT_VENV_PYTHON)
else
PYTHON ?= python3
endif

BACKEND_PORT ?= 8000

.PHONY: backend frontend both

backend:
	cd backend && $(PYTHON) -m uvicorn app.main:app --reload --port $(BACKEND_PORT)

frontend:
	cd frontend && npm run dev

both:
	$(MAKE) -j2 backend frontend
