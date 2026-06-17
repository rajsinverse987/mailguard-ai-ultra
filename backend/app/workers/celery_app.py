"""Celery app + periodic schedule."""

from __future__ import annotations

from celery import Celery
from celery.schedules import crontab

from app.config import settings

celery_app = Celery(
    "mailguard",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=[
        "app.workers.tasks_email",
        "app.workers.tasks_voice",
        "app.workers.tasks_whatsapp",
        "app.workers.tasks_briefings",
    ],
)

celery_app.conf.update(
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=4,
    task_default_queue="mailguard.default",
    task_routes={
        "app.workers.tasks_email.*": {"queue": "mailguard.email"},
        "app.workers.tasks_voice.*": {"queue": "mailguard.voice"},
        "app.workers.tasks_whatsapp.*": {"queue": "mailguard.whatsapp"},
        "app.workers.tasks_briefings.*": {"queue": "mailguard.briefings"},
    },
    broker_connection_retry_on_startup=True,
)

# Periodic schedule (UTC). Morning briefing 02:30 UTC ≈ 08:00 IST.
celery_app.conf.beat_schedule = {
    "morning-briefings": {
        "task": "app.workers.tasks_briefings.schedule_morning_briefings",
        "schedule": crontab(hour=2, minute=30),
    },
    "evening-summaries": {
        "task": "app.workers.tasks_briefings.schedule_evening_briefings",
        "schedule": crontab(hour=13, minute=30),  # 19:00 IST
    },
    "poll-all-accounts": {
        "task": "app.workers.tasks_email.poll_all_accounts",
        "schedule": crontab(minute="*/5"),
    },
}
