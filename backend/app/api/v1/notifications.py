"""Notification + voice endpoints."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import desc, select

from app.api.deps import CurrentUser, SessionDep
from app.config import settings
from app.models.email import Email
from app.models.notification import Notification
from app.models.voice_note import VoiceNote
from app.schemas.notification import NotificationOut, VoiceNoteOut
from app.services.messaging.dispatcher import WhatsAppDispatcher, format_rich_text
from app.services.voice.tts import VoiceComposer, get_tts
from app.workers.tasks_whatsapp import send_notifications_for_email

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=list[NotificationOut])
async def list_notifications(
    user: CurrentUser,
    db: SessionDep,
    limit: int = Query(50, ge=1, le=200),
) -> list[NotificationOut]:
    res = await db.execute(
        select(Notification)
        .where(Notification.user_id == user.id)
        .order_by(desc(Notification.created_at))
        .limit(limit)
    )
    return [NotificationOut.model_validate(n) for n in res.scalars().all()]


@router.post("/retry/{email_id}")
async def retry(email_id: uuid.UUID, user: CurrentUser) -> dict:
    send_notifications_for_email.delay(str(email_id))
    return {"queued": True, "email_id": str(email_id)}


@router.get("/whatsapp/status")
async def whatsapp_status(user: CurrentUser) -> dict:
    target = user.whatsapp_number or user.phone
    provider = settings.whatsapp_provider
    if provider == "meta":
        missing = [
            name
            for name, value in {
                "WHATSAPP_TOKEN": settings.whatsapp_token,
                "WHATSAPP_PHONE_ID": settings.whatsapp_phone_id,
            }.items()
            if not value
        ]
    else:
        missing = [
            name
            for name, value in {
                "TWILIO_ACCOUNT_SID": settings.twilio_account_sid,
                "TWILIO_AUTH_TOKEN": settings.twilio_auth_token,
                "TWILIO_WHATSAPP_FROM": settings.twilio_whatsapp_from,
            }.items()
            if not value
        ]
    return {
        "provider": provider,
        "configured": len(missing) == 0,
        "missing": missing,
        "target_number": target,
        "has_target_number": bool(target),
    }


@router.post("/whatsapp/latest", response_model=NotificationOut, status_code=201)
async def send_latest_whatsapp(user: CurrentUser, db: SessionDep) -> NotificationOut:
    target = user.whatsapp_number or user.phone
    if not target:
        raise HTTPException(
            status_code=400,
            detail="Add a phone or WhatsApp number in Settings before sending.",
        )

    email = (
        await db.execute(
            select(Email)
            .where(Email.user_id == user.id)
            .order_by(desc(Email.received_at))
            .limit(1)
        )
    ).scalar_one_or_none()
    if not email:
        raise HTTPException(status_code=404, detail="Add an email first, then send a WhatsApp log.")

    body = format_rich_text(
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
    notif = await WhatsAppDispatcher().send_text(
        db,
        user_id=user.id,
        email_id=email.id,
        to_number=target,
        body=body,
    )
    await db.commit()
    await db.refresh(notif)
    return NotificationOut.model_validate(notif)


async def _create_voice_note(db: SessionDep, user: CurrentUser, email: Email) -> VoiceNote:
    text = VoiceComposer.compose(
        user_name=user.full_name.split(" ")[0],
        analysis={
            "subject": email.subject,
            "sender": email.sender_email,
            "sender_name": email.sender_name,
            "sender_company": email.sender_company,
            "category": email.category,
            "priority": email.priority,
            "is_phishing": email.is_phishing,
            "threat_score": email.threat_score,
        },
        language="en",
    )
    audio_url = None
    engine = "browser"
    voice = "browser-speech"
    mime = "text/plain"
    size_bytes = len(text.encode("utf-8"))

    try:
        result = await get_tts().synthesize(
            text,
            language="en",
            gender=user.voice_gender or "female",
            preferred=user.preferred_voice or "personal_assistant",
            priority=email.priority,
            category=email.category,
        )
        engine = result["engine"]
        voice = result["voice"]
        mime = result["mime"]
        size_bytes = len(result["audio_bytes"])
    except Exception:
        pass

    note = VoiceNote(
        user_id=user.id,
        email_id=email.id,
        text=text,
        language="en",
        voice=voice,
        gender=user.voice_gender or "female",
        engine=engine,
        audio_url=audio_url,
        size_bytes=size_bytes,
        mime=mime,
    )
    db.add(note)
    await db.commit()
    await db.refresh(note)
    return note


@router.post("/voice/latest", response_model=VoiceNoteOut, status_code=201)
async def create_latest_voice_note(user: CurrentUser, db: SessionDep) -> VoiceNoteOut:
    email = (
        await db.execute(
            select(Email)
            .where(Email.user_id == user.id)
            .order_by(desc(Email.received_at))
            .limit(1)
        )
    ).scalar_one_or_none()
    if not email:
        raise HTTPException(status_code=404, detail="Add an email first, then generate a voice note.")
    note = await _create_voice_note(db, user, email)
    return VoiceNoteOut.model_validate(note)


@router.post("/voice/from-email/{email_id}", response_model=VoiceNoteOut, status_code=201)
async def create_voice_note_from_email(
    email_id: uuid.UUID, user: CurrentUser, db: SessionDep
) -> VoiceNoteOut:
    email = await db.get(Email, email_id)
    if not email or email.user_id != user.id:
        raise HTTPException(status_code=404, detail="email not found")
    note = await _create_voice_note(db, user, email)
    return VoiceNoteOut.model_validate(note)


@router.get("/voice", response_model=list[VoiceNoteOut])
async def list_voice_notes(
    user: CurrentUser, db: SessionDep, limit: int = Query(50, ge=1, le=200)
) -> list[VoiceNoteOut]:
    res = await db.execute(
        select(VoiceNote)
        .where(VoiceNote.user_id == user.id)
        .order_by(desc(VoiceNote.created_at))
        .limit(limit)
    )
    return [VoiceNoteOut.model_validate(v) for v in res.scalars().all()]
