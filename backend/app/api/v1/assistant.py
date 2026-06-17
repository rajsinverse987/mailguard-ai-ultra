"""AI chat assistant endpoint (text + voice)."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, SessionDep
from app.models.email import Email
from app.models.voice_note import VoiceNote
from app.schemas.email import ChatIn, ChatOut, EmailSummaryOut
from app.services.ai.translator import to_hindi
from app.services.vector.store import get_vector_store
from app.services.voice.tts import get_tts
from app.config import settings

router = APIRouter(prefix="/assistant", tags=["assistant"])

INTENTS = {
    "important": "Important emails today",
    "interview": "Interview invitations",
    "banking": "Banking alerts",
    "bills": "Unpaid bills",
    "phishing": "Phishing / fraud",
    "summary": "Daily summary",
}


def _detect_intent(q: str) -> str | None:
    ql = q.lower()
    for key, label in INTENTS.items():
        if key in ql or label.lower() in ql:
            return key
    return None


@router.post("/chat", response_model=ChatOut)
async def chat(payload: ChatIn, user: CurrentUser, db: SessionDep) -> ChatOut:
    intent = _detect_intent(payload.query)

    cited: list[EmailSummaryOut] = []
    if intent:
        filters = {
            "important": ("high", "critical"),
            "interview": ("interview_calls",),
            "banking": ("banking",),
            "bills": ("bills",),
            "phishing": None,
        }[intent]
        q = select(Email).where(Email.user_id == user.id)
        if filters:
            if intent == "important":
                q = q.where(Email.priority.in_(filters))
            else:
                q = q.where(Email.category.in_(filters))
        if intent == "phishing":
            q = q.where(Email.is_phishing.is_(True))
        q = q.order_by(desc(Email.received_at)).limit(5)
        rows = (await db.execute(q)).scalars().all()
        cited = [EmailSummaryOut.model_validate(r) for r in rows]
        answer = await _compose_intent_answer(intent, cited, user.preferred_language)
    else:
        vs = get_vector_store()
        hits = await vs.search(payload.query, k=5, filter_={"user_id": str(user.id)})
        for h in hits:
            try:
                e = await db.get(Email, uuid.UUID(h["id"]))
                if e and e.user_id == user.id:
                    cited.append(EmailSummaryOut.model_validate(e))
            except Exception:  # noqa: BLE001
                continue
        answer = await _compose_freeform_answer(payload.query, cited, user.preferred_language)

    answer_hi = await to_hindi(answer)
    voice_id: uuid.UUID | None = None
    if payload.voice_reply:
        tts = get_tts()
        spoken = await _voice_text(answer_hi, user.preferred_language or "hi")
        result = await tts.synthesize(
            spoken,
            language=user.preferred_language or "hi",
            gender=user.voice_gender or "female",
            preferred=user.preferred_voice or "personal_assistant",
        )
        note = VoiceNote(
            user_id=user.id,
            text=spoken,
            language=user.preferred_language or "hi",
            voice=result["voice"],
            gender=user.voice_gender or "female",
            engine=result["engine"],
            size_bytes=len(result["audio_bytes"]),
            mime=result["mime"],
        )
        db.add(note)
        await db.commit()
        voice_id = note.id

    return ChatOut(
        query=payload.query,
        answer=answer,
        answer_hi=answer_hi,
        cited_emails=cited,
        voice_note_id=voice_id,
    )


async def _compose_intent_answer(intent: str, emails: list[EmailSummaryOut], lang: str) -> str:
    if not emails:
        return "I didn't find anything matching that request."
    lines = [f"I found {len(emails)} matching emails."]
    for e in emails[:3]:
        sender = e.sender_company or e.sender_name or e.sender_email
        lines.append(f"• {sender}: {e.subject}")
    return "\n".join(lines)


async def _compose_freeform_answer(query: str, emails: list[EmailSummaryOut], lang: str) -> str:
    if not emails:
        return "I couldn't find any relevant emails. Could you rephrase?"
    top = emails[:3]
    parts = [f"Here are the most relevant emails for '{query}':"]
    for e in top:
        sender = e.sender_company or e.sender_name or e.sender_email
        summary = e.summary or e.subject
        parts.append(f"- {sender}: {summary}")
    return "\n".join(parts)


async def _voice_text(answer: str, lang: str) -> str:
    # Compact to 1-2 sentences for spoken delivery
    sentences = [s.strip() for s in answer.replace("\n", " ").split(".") if s.strip()]
    return ". ".join(sentences[:3]) + "."
