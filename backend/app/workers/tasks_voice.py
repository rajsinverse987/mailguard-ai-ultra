"""Voice synthesis background tasks."""

from __future__ import annotations

import asyncio
import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.db.session import SessionLocal
from app.models.email import Email
from app.models.user import User
from app.models.voice_note import VoiceNote
from app.services.voice.tts import VoiceComposer, get_tts
from app.workers.celery_app import celery_app

logger = get_logger(__name__)


def _run(coro):
    return asyncio.run(coro)


@celery_app.task(name="app.workers.tasks_voice.synthesize_for_email")
def synthesize_for_email(email_id: str, *, user_id: str | None = None) -> str:
    return _run(_synthesize_for_email_async(email_id))


async def _synthesize_for_email_async(email_id: str) -> str:
    eid = uuid.UUID(email_id)
    async with SessionLocal() as db:
        email = await db.get(Email, eid)
        if not email:
            return "missing"
        user = await db.get(User, email.user_id)
        if not user:
            return "no_user"

        # Build spoken text
        analysis = {
            "subject": email.subject,
            "sender": email.sender_email,
            "sender_name": email.sender_name,
            "sender_company": email.sender_company,
            "category": email.category,
            "priority": email.priority,
            "is_phishing": email.is_phishing,
            "threat_score": email.threat_score,
            "summary": email.summary,
            "summary_hi": email.summary_hi,
        }
        text_hi = VoiceComposer.compose(
            user_name=user.full_name.split(" ")[0], analysis=analysis, language=user.preferred_language or "hi"
        )

        tts = get_tts()
        result = await tts.synthesize(
            text_hi,
            language=user.preferred_language or "hi",
            gender=user.voice_gender or "female",
            preferred=user.preferred_voice or "personal_assistant",
            priority=email.priority,
            category=email.category,
        )

        note = VoiceNote(
            user_id=user.id,
            email_id=email.id,
            text=text_hi,
            text_hi=text_hi,
            language=user.preferred_language or "hi",
            voice=result["voice"],
            gender=user.voice_gender or "female",
            engine=result["engine"],
            audio_url=None,  # uploaded by whatsapp task
            storage_key=None,
            duration_ms=result.get("duration_ms"),
            size_bytes=len(result["audio_bytes"]),
            mime=result["mime"],
        )
        db.add(note)
        await db.commit()
        return str(note.id)
