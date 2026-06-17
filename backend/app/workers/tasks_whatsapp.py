"""WhatsApp notification tasks."""

from __future__ import annotations

import asyncio
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.db.session import SessionLocal
from app.models.email import Email
from app.models.user import User
from app.models.voice_note import VoiceNote
from app.services.messaging.dispatcher import WhatsAppDispatcher, format_rich_text
from app.services.voice.tts import VoiceComposer, get_tts
from app.workers.celery_app import celery_app

logger = get_logger(__name__)


def _run(coro):
    return asyncio.run(coro)


@celery_app.task(name="app.workers.tasks_whatsapp.send_notifications_for_email")
def send_notifications_for_email(email_id: str) -> str:
    return _run(_send_notifications_for_email_async(email_id))


async def _send_notifications_for_email_async(email_id: str) -> str:
    eid = uuid.UUID(email_id)
    async with SessionLocal() as db:
        email = await db.get(Email, eid)
        if not email:
            return "missing"
        user = await db.get(User, email.user_id)
        if not user or not user.whatsapp_number:
            return "no_whatsapp"

        dispatcher = WhatsAppDispatcher()

        # 1. Text summary
        if user.enable_text_alerts:
            text = format_rich_text(
                {
                    "subject": email.subject,
                    "sender": email.sender_email,
                    "sender_name": email.sender_name,
                    "sender_company": email.sender_company,
                    "summary": email.summary,
                    "summary_hi": email.summary_hi,
                    "priority": email.priority,
                    "action_items": email.action_items,
                    "due_dates": email.due_dates,
                    "is_phishing": email.is_phishing,
                    "threat_score": email.threat_score,
                },
                language=user.preferred_language or "en",
            )
            await dispatcher.send_text(
                db, user_id=user.id, to_number=user.whatsapp_number, body=text
            )

        # 2. Voice note
        if user.enable_voice_alerts:
            tts = get_tts()
            analysis = {
                "subject": email.subject,
                "sender": email.sender_email,
                "sender_name": email.sender_name,
                "sender_company": email.sender_company,
                "category": email.category,
                "priority": email.priority,
                "is_phishing": email.is_phishing,
                "threat_score": email.threat_score,
            }
            spoken_hi = VoiceComposer.compose(
                user_name=user.full_name.split(" ")[0],
                analysis=analysis,
                language=user.preferred_language or "hi",
            )
            result = await tts.synthesize(
                spoken_hi,
                language=user.preferred_language or "hi",
                gender=user.voice_gender or "female",
                preferred=user.preferred_voice or "personal_assistant",
                priority=email.priority,
                category=email.category,
            )

            note = VoiceNote(
                user_id=user.id,
                email_id=email.id,
                text=spoken_hi,
                language=user.preferred_language or "hi",
                voice=result["voice"],
                gender=user.voice_gender or "female",
                engine=result["engine"],
                audio_url=None,
                size_bytes=len(result["audio_bytes"]),
                mime=result["mime"],
            )
            db.add(note)
            await db.flush()

            await dispatcher.send_audio(
                db,
                user_id=user.id,
                to_number=user.whatsapp_number,
                audio_bytes=result["audio_bytes"],
                mime=result["mime"],
            )

        email.notified = True
        await db.commit()
    return "sent"
