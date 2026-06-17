"""High-level WhatsApp dispatcher: picks provider, formats rich text, sends voice."""

from __future__ import annotations

import asyncio
import base64
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.logging import get_logger
from app.models.notification import Notification
from app.services.messaging.twilio import TwilioWhatsAppClient
from app.services.messaging.whatsapp import MetaWhatsAppClient

logger = get_logger(__name__)


# --- Text formatter -------------------------------------------------------
def format_rich_text(analysis: dict[str, Any], language: str = "en") -> str:
    """Format a WhatsApp-friendly text summary with emojis."""
    priority_icon = {
        "critical": "🚨",
        "high": "⚠️",
        "medium": "📬",
        "low": "ℹ️",
    }.get(analysis.get("priority", "medium"), "📬")

    sender = (
        analysis.get("sender_company")
        or analysis.get("sender_name")
        or analysis.get("sender")
        or "Unknown"
    )
    subject = analysis.get("subject") or "(no subject)"
    summary = (
        analysis.get("summary_hi") if language == "hi" else analysis.get("summary")
    ) or analysis.get("summary", "")

    action_items = analysis.get("action_items") or []
    due_dates = analysis.get("due_dates") or []

    lines = [
        f"{priority_icon} *New Email*",
        f"*From:* {sender}",
        f"*Subject:* {subject}",
        "",
        "*Summary:*",
        summary,
    ]
    if due_dates:
        lines.append("")
        lines.append(f"*Deadline:* {', '.join(due_dates)}")
    if action_items:
        lines.append("")
        lines.append("*Action Required:*")
        lines.extend(f"• {a}" for a in action_items[:5])
    if analysis.get("is_phishing") or analysis.get("threat_score", 0) >= 60:
        lines.append("")
        threat = analysis.get("threat_score", 0)
        lines.append(f"🛡 *Threat Score:* {threat}/100 — handle with caution.")
    return "\n".join(lines)


# --- Dispatcher -----------------------------------------------------------
class WhatsAppDispatcher:
    def __init__(self) -> None:
        self.meta = MetaWhatsAppClient()
        self.twilio = TwilioWhatsAppClient()

    async def send_text(
        self,
        db: AsyncSession,
        *,
        user_id: uuid.UUID,
        to_number: str,
        body: str,
        email_id: uuid.UUID | None = None,
    ) -> Notification:
        provider = settings.whatsapp_provider
        response: dict[str, Any] = {"skipped": True, "reason": "no provider configured"}
        delivered = False
        error: str | None = None

        try:
            if provider == "meta" and self.meta.configured:
                response = await self.meta.send_text(to_number, body)
                delivered = response.get("status_code") == 200
            elif provider == "twilio" and self.twilio.configured:
                response = await self.twilio.send_text(to_number, body)
                delivered = response.get("status_code") == 200
            else:
                error = _provider_missing_error(provider)
                logger.warning("whatsapp_provider_not_configured", provider=provider)
        except Exception as exc:  # noqa: BLE001
            error = str(exc)
            logger.error("whatsapp_send_failed", error=error)

        notif = Notification(
            id=uuid.uuid4(),
            user_id=user_id,
            email_id=email_id,
            channel="whatsapp_text",
            provider=provider,
            to_number=to_number,
            payload={"body": body},
            provider_response=response,
            delivered=delivered,
            error=error,
            status="delivered" if delivered else "failed",
        )
        db.add(notif)
        await db.flush()
        return notif

    async def send_audio(
        self,
        db: AsyncSession,
        *,
        user_id: uuid.UUID,
        to_number: str,
        audio_bytes: bytes,
        mime: str = "audio/mpeg",
        email_id: uuid.UUID | None = None,
    ) -> Notification:
        provider = settings.whatsapp_provider
        delivered = False
        error: str | None = None
        response: dict[str, Any] = {"skipped": True}

        try:
            if provider == "meta" and self.meta.configured:
                media_id = await self.meta.upload_audio(audio_bytes, mime=mime)
                if media_id:
                    response = await self.meta.send_audio(to_number, f"https://lookaside.fbsbx.com/media/{media_id}")
                    delivered = response.get("status_code") == 200
                else:
                    error = "upload failed"
            elif provider == "twilio" and self.twilio.configured:
                media_url = await self._upload_to_public_cdn(audio_bytes)
                if media_url:
                    response = await self.twilio.send_audio(to_number, media_url)
                    delivered = response.get("status_code") == 200
                else:
                    error = "no media url"
            else:
                error = _provider_missing_error(provider)
        except Exception as exc:  # noqa: BLE001
            error = str(exc)
            logger.error("whatsapp_audio_failed", error=error)

        notif = Notification(
            id=uuid.uuid4(),
            user_id=user_id,
            email_id=email_id,
            channel="whatsapp_voice",
            provider=provider,
            to_number=to_number,
            payload={"mime": mime, "size": len(audio_bytes)},
            provider_response=response,
            delivered=delivered,
            error=error,
            status="delivered" if delivered else "failed",
        )
        db.add(notif)
        await db.flush()
        return notif

    async def _upload_to_public_cdn(self, audio: bytes) -> str | None:
        # Production: upload to S3 + return signed URL
        # Here we return None to indicate "use Meta upload instead"
        return None


_singleton: WhatsAppDispatcher | None = None


def get_dispatcher() -> WhatsAppDispatcher:
    global _singleton
    if _singleton is None:
        _singleton = WhatsAppDispatcher()
    return _singleton


def _provider_missing_error(provider: str) -> str:
    if provider == "meta":
        return "Meta WhatsApp is not configured. Missing WHATSAPP_TOKEN or WHATSAPP_PHONE_ID."
    if provider == "twilio":
        return (
            "Twilio WhatsApp is not configured. Missing TWILIO_ACCOUNT_SID, "
            "TWILIO_AUTH_TOKEN, or TWILIO_WHATSAPP_FROM."
        )
    return f"WhatsApp provider '{provider}' is not configured."
