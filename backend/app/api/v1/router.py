"""v1 API aggregator."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1 import accounts, analytics, assistant, auth, briefings, emails, fraud, notifications, webhooks

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(accounts.router)
api_router.include_router(emails.router)
api_router.include_router(notifications.router)
api_router.include_router(fraud.router)
api_router.include_router(assistant.router)
api_router.include_router(analytics.router)
api_router.include_router(briefings.router)
api_router.include_router(webhooks.router)
