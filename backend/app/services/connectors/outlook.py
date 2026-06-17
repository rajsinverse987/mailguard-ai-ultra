"""Microsoft Graph (Outlook) connector."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any

import httpx

from app.core.logging import get_logger
from app.services.connectors.base import BaseConnector, RawEmail

logger = get_logger(__name__)


class OutlookConnector(BaseConnector):
    provider = "outlook"

    GRAPH = "https://graph.microsoft.com/v1.0"

    def __init__(self, *, access_token: str) -> None:
        self.access_token = access_token

    @property
    def _auth_headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.access_token}"}

    async def fetch_new(self, *, since: datetime | None = None) -> list[RawEmail]:
        url = f"{self.GRAPH}/me/messages"
        params: dict[str, Any] = {
            "$top": 50,
            "$filter": "isRead eq false",
            "$orderby": "receivedDateTime desc",
            "$select": "id,subject,from,toRecipients,ccRecipients,receivedDateTime,bodyPreview,body,internetMessageId",
        }
        if since:
            params["$filter"] = (
                f"receivedDateTime ge {since.isoformat().replace('+00:00', 'Z')}"
            )
        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.get(url, headers=self._auth_headers, params=params)
            if r.status_code == 401:
                raise PermissionError("outlook_token_expired")
            r.raise_for_status()
            data = r.json()
        return [self._parse_message(m) for m in data.get("value", [])]

    async def fetch_message(self, message_id: str) -> RawEmail:
        url = f"{self.GRAPH}/me/messages/{message_id}"
        params = {"$select": "id,subject,from,toRecipients,ccRecipients,receivedDateTime,bodyPreview,body,conversationId,internetMessageId"}
        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.get(url, headers=self._auth_headers, params=params)
            r.raise_for_status()
            return self._parse_message(r.json())

    async def setup_watch(self) -> dict[str, Any]:
        url = f"{self.GRAPH}/subscriptions"
        body = {
            "changeType": "created",
            "notificationUrl": "https://example.com/api/v1/webhooks/outlook",
            "resource": "/me/messages",
            "expirationDateTime": "2099-12-31T00:00:00Z",
            "clientState": "mailguard-ai",
        }
        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.post(url, headers=self._auth_headers, json=body)
            r.raise_for_status()
            return r.json()

    def _parse_message(self, msg: dict[str, Any]) -> RawEmail:
        sender = msg.get("from", {}).get("emailAddress", {})
        sender_email = sender.get("address", "")
        sender_name = sender.get("name")
        to = [
            r["emailAddress"]["address"]
            for r in msg.get("toRecipients", [])
            if r.get("emailAddress")
        ]
        cc = [
            r["emailAddress"]["address"]
            for r in msg.get("ccRecipients", [])
            if r.get("emailAddress")
        ]
        body = msg.get("body", {}) or {}
        body_content = body.get("content", "")
        content_type = body.get("contentType", "text")
        body_text = body_content if content_type == "text" else _strip_html(body_content)
        links = list(set(re.findall(r"https?://[^\s\"'<>]+", body_content)))

        received_at_raw = msg.get("receivedDateTime")
        try:
            received_at = datetime.fromisoformat(received_at_raw.replace("Z", "+00:00"))
        except Exception:  # noqa: BLE001
            received_at = datetime.now(timezone.utc)

        return RawEmail(
            provider=self.provider,
            message_id=msg.get("internetMessageId") or msg.get("id"),
            thread_id=msg.get("conversationId"),
            subject=msg.get("subject") or "",
            sender_email=sender_email,
            sender_name=sender_name,
            to=to,
            cc=cc,
            body_text=body_text,
            body_html=body_content if content_type == "html" else None,
            snippet=msg.get("bodyPreview"),
            received_at=received_at,
            links=links,
            raw=msg,
        )


def _strip_html(html: str) -> str:
    html = re.sub(r"<style[\s\S]*?</style>", "", html, flags=re.IGNORECASE)
    html = re.sub(r"<script[\s\S]*?</script>", "", html, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", html)
    return re.sub(r"\s+", " ", text).strip()
