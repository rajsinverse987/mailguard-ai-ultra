"""Scheduled briefing tasks (morning + evening)."""

from __future__ import annotations

import asyncio
from datetime import date, datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.db.session import SessionLocal
from app.models.user import User
from app.services.briefings import generate_morning_briefing, generate_evening_briefing
from app.services.messaging.dispatcher import WhatsAppDispatcher
from app.services.voice.tts import get_tts
from app.workers.celery_app import celery_app
from app.workers.celery_app import celery_app

logger = get_logger(__name__)


def _run(coro):
    return asyncio.run(coro)


@celery_app.task(name="app.workers.tasks_briefings.schedule_morning_briefings")
def schedule_morning_briefings() -> int:
    return _run(_schedule_morning_briefings_async())


@celery_app.task(name="app.workers.tasks_briefings.schedule_evening_briefings")
def schedule_evening_briefings() -> int:
    return _run(_schedule_evening_briefings_async())


async def _schedule_morning_briefings_async() -> int:
    today = date.today()
    sent = 0
    async with SessionLocal() as db:
        users = (await db.execute(select(User).where(User.is_active.is_(True)))).scalars().all()
        for user in users:
            try:
                briefing = await generate_morning_briefing(db, user, day=today)
                await _deliver_briefing(db, user, briefing)
                sent += 1
            except Exception as exc:  # noqa: BLE001
                logger.warning("morning_briefing_failed", user_id=str(user.id), error=str(exc))
        await db.commit()
    return sent


async def _schedule_evening_briefings_async() -> int:
    today = date.today()
    sent = 0
    async with SessionLocal() as db:
        users = (await db.execute(select(User).where(User.is_active.is_(True)))).scalars().all()
        for user in users:
            try:
                briefing = await generate_evening_briefing(db, user, day=today)
                await _deliver_briefing(db, user, briefing)
                sent += 1
            except Exception as exc:  # noqa: BLE001
                logger.warning("evening_briefing_failed", user_id=str(user.id), error=str(exc))
        await db.commit()
    return sent


async def _deliver_briefing(db: AsyncSession, user: User, briefing) -> None:
    if not user.whatsapp_number:
        return
    tts = get_tts()
    audio = await tts.synthesize(
        briefing.text,
        language=user.preferred_language or "hi",
        gender=user.voice_gender or "female",
        preferred=user.preferred_voice or "personal_assistant",
    )
    dispatcher = WhatsAppDispatcher()
    await dispatcher.send_audio(
        db,
        user_id=user.id,
        to_number=user.whatsapp_number,
        audio_bytes=audio["audio_bytes"],
        mime=audio["mime"],
    )
    briefing.delivered = True
