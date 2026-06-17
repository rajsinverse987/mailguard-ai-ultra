#!/usr/bin/env bash
# Convenience script to run MailGuard AI Ultra locally without Docker.

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

# Backend
(cd "$ROOT/backend" && python -m venv .venv 2>/dev/null || true)
(cd "$ROOT/backend" && source .venv/bin/activate && pip install -r requirements.txt)
(cd "$ROOT/backend" && source .venv/bin/activate && alembic upgrade head || true)
(cd "$ROOT/backend" && source .venv/bin/activate && uvicorn app.main:app --reload --port 8000 &)
(cd "$ROOT/backend" && source .venv/bin/activate && celery -A app.workers.celery_app worker -l info &)

# Frontend
(cd "$ROOT/frontend" && npm install)
(cd "$ROOT/frontend" && npm run dev)

wait
