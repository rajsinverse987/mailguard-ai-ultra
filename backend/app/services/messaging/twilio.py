"""Twilio WhatsApp fallback."""

from __future__ import annotations

from typing import Any

from app.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class TwilioWhatsAppClient:
    def __init__(self) -> None:
        self.from_ = settings.twilio_whatsapp_from

    @property
    def configured(self) -> bool:
        return bool(
            settings.twilio_account_sid
            and settings.twilio_auth_token
            and self.from_
        )

    async def send_text(self, to: str, text: str) -> dict[str, Any]:
        if not self.configured:
            raise RuntimeError("Twilio not configured")
        try:
            from twilio.rest import Client
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError("twilio library not installed") from exc

        client = Client(settings.twilio_account_sid, settings.twilio_auth_token)
        msg = client.messages.create(
            body=text,
            from_=f"whatsapp:{self.from_}",
            to=f"whatsapp:{to}",
        )
        return {"status_code": 200, "response": {"sid": msg.sid, "status": msg.status}}

    async def send_audio(self, to: str, media_url: str) -> dict[str, Any]:
        if not self.configured:
            raise RuntimeError("Twilio not configured")
        from twilio.rest import Client

        client = Client(settings.twilio_account_sid, settings.twilio_auth_token)
        msg = client.messages.create(
            media_url=[media_url],
            from_=f"whatsapp:{self.from_}",
            to=f"whatsapp:{to}",
        )
        return {"status_code": 200, "response": {"sid": msg.sid, "status": msg.status}}
