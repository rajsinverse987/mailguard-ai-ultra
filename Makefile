.PHONY: help install backend frontend test lint migrate run dev up down logs

help:
	@echo "MailGuard AI Ultra — make targets"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN{FS=":.*?## "}{printf "  %-18s %s\n",$$1,$$2}'

install: ## Install backend + frontend deps
	cd backend && python -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt
	cd frontend && npm install

backend: ## Run backend dev server
	cd backend && . .venv/bin/activate && uvicorn app.main:app --reload --port 8000

frontend: ## Run frontend dev server
	cd frontend && npm run dev

worker: ## Run celery worker
	cd backend && . .venv/bin/activate && celery -A app.workers.celery_app worker -l info

migrate: ## Run Alembic migrations
	cd backend && . .venv/bin/activate && alembic upgrade head

test: ## Run all tests
	cd backend && . .venv/bin/activate && pytest -q
	cd frontend && npm test --silent

lint: ## Lint backend + frontend
	cd backend && . .venv/bin/activate && ruff check .
	cd frontend && npm run lint

up: ## Start docker compose stack
	docker compose up --build -d

down: ## Stop docker compose stack
	docker compose down

logs: ## Tail docker logs
	docker compose logs -f --tail=100
