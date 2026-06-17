"""Gmail connector using google-api-python-client + Pub/Sub watch."""

from __future__ import annotations

import base64
import re
from datetime import datetime, timezone
from typing import Any

import httpx

from app.config import settings
from app.core.crypto import cipher
from app.core.logging import get_logger
from app.services.connectors.base import BaseConnector, RawEmail

logger = get_logger(__name__)


class GmailConnector(BaseConnector):
    provider = "gmail"

    GMAIL_API = "https://gmail.googleapis.com/gmail/v1/users/me"

    def __init__(self, *, access_token: str, refresh_token: str | None = None) -> None:
        self.access_token = access_token
        self.refresh_token = refresh_token

    @property
    def _auth_headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

    async def fetch_new(self, *, since: datetime | None = None) -> list[RawEmail]:
        query = "is:unread"
        if since:
            query += f" after:{int(since.timestamp())}"
        url = f"{self.GMAIL_API}/messages"
        params = {"q": query, "maxResults": 50}
        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.get(url, headers=self._auth_headers, params=params)
            if r.status_code == 401:
                raise PermissionError("gmail_token_expired")
            r.raise_for_status()
            data = r.json()
        ids = [m["id"] for m in data.get("messages", [])]
        return [await self.fetch_message(i) for i in ids]

    async def fetch_message(self, message_id: str) -> RawEmail:
        url = f"{self.GMAIL_API}/messages/{message_id}"
        params = {"format": "full"}
        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.get(url, headers=self._auth_headers, params=params)
            r.raise_for_status()
            return self._parse_message(r.json())

    async def setup_watch(self) -> dict[str, Any]:
        url = f"{self.GMAIL_API}/watch"
        body = {
            "topicName": settings.gmail_pubsub_topic,
            "labelIds": ["INBOX"],
        }
        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.post(url, headers=self._auth_headers, json=body)
            r.raise_for_status()
            return r.json()

    def _parse_message(self, msg: dict[str, Any]) -> RawEmail:
        payload = msg.get("payload", {})
        headers = {h["name"].lower(): h["value"] for h in payload.get("headers", [])}

        sender_full = headers.get("from", "")
        sender_email, sender_name = self._parseaddr(sender_full)
        to_list = self._parseaddr_list(headers.get("to", ""))
        cc_list = self._parseaddr_list(headers.get("cc", ""))
        subject = headers.get("subject", "")
        date_str = headers.get("date", "")

        body_text, body_html, links = self._walk_parts(payload)

        received_at = self._parse_date(date_str) or _now()

        attachments = [
            {
                "filename": p.get("filename"),
                "mime": p.get("mimeType"),
                "size": p.get("body", {}).get("size"),
            }
            for p in self._iter_parts(payload)
            if p.get("filename")
        ]

        return RawEmail(
            provider=self.provider,
            message_id=msg["id"],
            thread_id=msg.get("threadId"),
            subject=subject,
            sender_email=sender_email,
            sender_name=sender_name,
            to=to_list,
            cc=cc_list,
            body_text=body_text,
            body_html=body_html,
            snippet=msg.get("snippet"),
            received_at=received_at,
            labels=msg.get("labelIds", []),
            links=links,
            attachments=attachments,
            raw=msg,
        )

    @staticmethod
    def _parseaddr(value: str) -> tuple[str, str | None]:
        match = re.search(r"<([^>]+)>", value)
        if match:
            email = match.group(1).strip()
            name = value.split("<", 1)[0].strip().strip('"') or None
            return email, name
        return value.strip(), None

    @staticmethod
    def _parseaddr_list(value: str) -> list[str]:
        return [a.strip() for a in re.split(r",\s*", value) if a.strip()]

    def _walk_parts(self, payload: dict[str, Any]) -> tuple[str, str | None, list[str]]:
        text_parts: list[str] = []
        html_parts: list[str] = []
        links: set[str] = set()

        def walk(part: dict[str, Any]) -> None:
            mime = part.get("mimeType", "")
            body = part.get("body", {})
            data = body.get("data")
            if data:
                decoded = base64.urlsafe_b64decode(data + "=" * (-len(data) % 4)).decode(
                    "utf-8", errors="replace"
                )
                if mime == "text/plain":
                    text_parts.append(decoded)
                elif mime == "text/html":
                    html_parts.append(decoded)
                    for url in re.findall(r"https?://[^\s\"'<>]+", decoded):
                        links.add(url)
            for sub in part.get("parts", []) or []:
                walk(sub)

        walk(payload)
        return "\n".join(text_parts), "\n".join(html_parts) or None, list(links)

    def _iter_parts(self, payload: dict[str, Any]):
        yield payload
        for sub in payload.get("parts", []) or []:
            yield from self._iter_parts(sub)

    @staticmethod
    def _parse_date(s: str) -> datetime | None:
        from email.utils import parsedate_to_datetime

        try:
            dt = parsedate_to_datetime(s)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
        except Exception:  # noqa: BLE001
            return None


def _now() -> datetime:
    return datetime.now(timezone.utc)


def encrypt_refresh_token(plain: str) -> str:
    return cipher.encrypt(plain)


def decrypt_refresh_token(token: str) -> str:
    return cipher.decrypt(token)
