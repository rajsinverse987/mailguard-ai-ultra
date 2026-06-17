"""WhatsApp Business API (Meta Cloud) client."""

from __future__ import annotations

import httpx

from app.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class MetaWhatsAppClient:
    BASE = "https://graph.facebook.com/v20.0"

    def __init__(self) -> None:
        self.phone_id = settings.whatsapp_phone_id
        self.token = settings.whatsapp_token

    @property
    def configured(self) -> bool:
        return bool(self.phone_id and self.token)

    async def send_text(self, to: str, text: str) -> dict:
        url = f"{self.BASE}/{self.phone_id}/messages"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }
        body = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "text",
            "text": {"body": text, "preview_url": False},
        }
        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.post(url, headers=headers, json=body)
            data = r.json() if r.headers.get("content-type", "").startswith("application/json") else {"raw": r.text}
            return {"status_code": r.status_code, "response": data}

    async def send_audio(self, to: str, audio_url: str) -> dict:
        url = f"{self.BASE}/{self.phone_id}/messages"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }
        body = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "audio",
            "audio": {"link": audio_url},
        }
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.post(url, headers=headers, json=body)
            data = r.json() if r.headers.get("content-type", "").startswith("application/json") else {"raw": r.text}
            return {"status_code": r.status_code, "response": data}

    async def upload_audio(self, audio_bytes: bytes, mime: str = "audio/mpeg") -> str | None:
        """Upload audio to Meta and return a media id (used in subsequent send)."""
        url = f"{self.BASE}/{self.phone_id}/media"
        headers = {"Authorization": f"Bearer {self.token}"}
        files = {"file": ("voice.mp3", audio_bytes, mime)}
        async with httpx.AsyncClient(timeout=60) as client:
            r = await client.post(url, headers=headers, files=files)
            if r.status_code >= 400:
                logger.warning("whatsapp_upload_failed", status=r.status_code, body=r.text)
                return None
            return r.json().get("id")
