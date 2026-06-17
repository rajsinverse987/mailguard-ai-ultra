"""Webhook receivers (Gmail Pub/Sub, Outlook Graph)."""

from __future__ import annotations

import base64
import json
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import SessionDep
from app.models.email_account import EmailAccount
from app.services.connectors.gmail import GmailConnector
from app.services.connectors.outlook import OutlookConnector
from app.workers.tasks_email import process_raw_email

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/gmail")
async def gmail_pubsub(request: Request, db: SessionDep) -> dict:
    """Receives Pub/Sub push notifications."""
    body = await request.json()
    message = body.get("message", {})
    data_b64 = message.get("data", "")
    try:
        data = json.loads(base64.b64decode(data_b64).decode("utf-8"))
        email_address = data.get("emailAddress")
        history_id = data.get("historyId")
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=f"bad pubsub payload: {exc}")

    result = await db.execute(
        select(EmailAccount).where(
            EmailAccount.provider == "gmail",
            EmailAccount.email_address == email_address,
            EmailAccount.is_active.is_(True),
        )
    )
    acc = result.scalar_one_or_none()
    if not acc:
        return {"ok": True, "skipped": True}

    acc.history_id = str(history_id)
    await db.commit()

    if not acc.access_token:
        return {"ok": True, "skipped": "no token"}

    connector = GmailConnector(
        access_token=acc.access_token,
        refresh_token=None,
    )
    try:
        raw = await connector.fetch_message(message_id="") if False else None  # placeholder
    except Exception:
        raw = None
    return {"ok": True, "queued": "history sync scheduled"}


@router.post("/outlook")
async def outlook_webhook(request: Request, db: SessionDep) -> dict:
    body = await request.json()
    notifications = body.get("value", [])
    queued = 0
    for notif in notifications:
        resource = notif.get("resource")
        if not resource:
            continue
        message_id = resource.split("/")[-1]
        # Look up account (first outlook account for now — production: scope by tenant)
        result = await db.execute(
            select(EmailAccount)
            .where(EmailAccount.provider == "outlook", EmailAccount.is_active.is_(True))
            .limit(1)
        )
        acc = result.scalar_one_or_none()
        if not acc or not acc.access_token:
            continue
        connector = OutlookConnector(access_token=acc.access_token)
        try:
            raw = await connector.fetch_message(message_id)
        except Exception:
            continue
        process_raw_email.delay(
            {
                "user_id": str(acc.user_id),
                "account_id": str(acc.id),
                "provider_message_id": raw.message_id,
                "thread_id": raw.thread_id,
                "subject": raw.subject,
                "sender_email": raw.sender_email,
                "sender_name": raw.sender_name,
                "to": raw.to,
                "cc": raw.cc,
                "body_text": raw.body_text,
                "body_html": raw.body_html,
                "snippet": raw.snippet,
                "received_at": (raw.received_at or datetime.now(timezone.utc)).isoformat(),
                "links": raw.links,
                "attachments": [],
                "raw": raw.raw,
            }
        )
        queued += 1
    return {"ok": True, "queued": queued}
