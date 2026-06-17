"""Background email processing pipeline."""

from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.db.session import SessionLocal
from app.models.email import Email
from app.models.email_account import EmailAccount
from app.services.ai.analyzer import get_analyzer
from app.services.ai.fraud_detector import analyze_threat
from app.services.connectors.gmail import GmailConnector, decrypt_refresh_token
from app.services.connectors.outlook import OutlookConnector
from app.services.vector.store import get_vector_store
from app.workers.celery_app import celery_app

logger = get_logger(__name__)


def _run(coro):
    return asyncio.run(coro)


@celery_app.task(name="app.workers.tasks_email.process_raw_email")
def process_raw_email(payload: dict[str, Any]) -> str:
    """Process an already-fetched email payload."""
    return _run(_process_raw_email_async(payload))


async def _process_raw_email_async(payload: dict[str, Any]) -> str:
    user_id = uuid.UUID(payload["user_id"])
    account_id = uuid.UUID(payload["account_id"])
    async with SessionLocal() as db:
        existing = await db.execute(
            select(Email).where(
                Email.provider_message_id == payload["provider_message_id"],
                Email.user_id == user_id,
            )
        )
        if existing.scalar_one_or_none():
            return "duplicate"

        # AI analysis
        analyzer = get_analyzer()
        analysis = await analyzer.analyze(
            subject=payload["subject"],
            sender=payload["sender_email"],
            body=payload.get("body_text", ""),
            received_at=_parse_dt(payload.get("received_at")),
        )

        # Fraud detection
        threat = await analyze_threat(
            {
                "sender_email": payload["sender_email"],
                "sender_name": payload.get("sender_name"),
                "subject": payload["subject"],
                "body_text": payload.get("body_text", ""),
                "links": payload.get("links", []),
            }
        )

        email = Email(
            user_id=user_id,
            account_id=account_id,
            provider_message_id=payload["provider_message_id"],
            thread_id=payload.get("thread_id"),
            subject=payload["subject"],
            sender_email=payload["sender_email"],
            sender_name=payload.get("sender_name"),
            sender_company=analysis.get("sender_company"),
            to_recipients=payload.get("to", []),
            cc_recipients=payload.get("cc", []),
            body_text=payload.get("body_text", ""),
            body_html=payload.get("body_html"),
            snippet=payload.get("snippet"),
            received_at=_parse_dt(payload.get("received_at")) or datetime.now(timezone.utc),
            category=analysis["category"],
            priority=analysis["priority"],
            sentiment=analysis.get("sentiment", "neutral"),
            intent=analysis.get("intent"),
            confidence=analysis["confidence"],
            summary=analysis.get("summary"),
            summary_hi=analysis.get("summary_hi"),
            action_items=analysis.get("action_items", []),
            due_dates=analysis.get("due_dates", []),
            meeting_requests=analysis.get("meeting_requests", []),
            tracking_numbers=analysis.get("tracking_numbers", []),
            invoice_amounts=analysis.get("invoice_amounts", []),
            otp_codes=analysis.get("otp_codes", []),
            payment_requests=analysis.get("payment_requests", []),
            links=payload.get("links", []),
            attachments=payload.get("attachments", []),
            labels=analysis.get("labels", []),
            is_phishing=bool(threat.get("is_phishing")),
            is_spam=bool(threat.get("is_scam")),
            threat_score=float(threat.get("threat_score", 0)),
            threat_reason=threat.get("reasoning"),
            processed=True,
            raw={"analysis": analysis, "threat": threat, "raw": payload.get("raw", {})},
        )
        db.add(email)
        await db.flush()

        # Persist fraud alert if needed
        if threat.get("threat_score", 0) >= 60:
            from app.models.fraud_alert import FraudAlert

            alert = FraudAlert(
                user_id=user_id,
                email_id=email.id,
                threat_score=threat["threat_score"],
                severity=threat.get("severity", "high"),
                is_phishing=bool(threat.get("is_phishing")),
                is_scam=bool(threat.get("is_scam")),
                reasons=threat.get("reasons", []),
                suspicious_links=threat.get("suspicious_links", []),
                indicators=threat.get("indicators", {}),
                reasoning=threat.get("reasoning"),
            )
            db.add(alert)

        await db.commit()

        # Upsert embedding
        vs = get_vector_store()
        await vs.upsert(
            doc_id=str(email.id),
            text=f"{email.subject}\n\n{email.body_text[:2000]}",
            metadata={
                "user_id": str(user_id),
                "category": email.category,
                "priority": email.priority,
                "subject": email.subject,
                "sender": email.sender_email,
            },
        )

        # Trigger downstream notifications for important emails
        if email.priority in {"high", "critical"}:
            from app.workers.tasks_whatsapp import send_notifications_for_email

            send_notifications_for_email.delay(str(email.id))

    return str(email.id)


@celery_app.task(name="app.workers.tasks_email.poll_all_accounts")
def poll_all_accounts() -> int:
    """Periodic poll fallback for accounts without webhook support."""
    return _run(_poll_all_accounts_async())


async def _poll_all_accounts_async() -> int:
    processed = 0
    async with SessionLocal() as db:
        result = await db.execute(
            select(EmailAccount).where(EmailAccount.is_active.is_(True))
        )
        accounts = result.scalars().all()
        for acc in accounts:
            try:
                processed += await _poll_account(db, acc)
            except Exception as exc:  # noqa: BLE001
                logger.warning("poll_account_failed", account_id=str(acc.id), error=str(exc))
    return processed


async def _poll_account(db: AsyncSession, acc: EmailAccount) -> int:
    if acc.provider == "gmail":
        if not acc.access_token:
            return 0
        access = acc.access_token  # already decrypted on read
        refresh = decrypt_refresh_token(acc.refresh_token) if acc.refresh_token else None
        connector = GmailConnector(access_token=access, refresh_token=refresh)
    elif acc.provider == "outlook":
        if not acc.access_token:
            return 0
        connector = OutlookConnector(access_token=acc.access_token)
    else:
        return 0

    raw_emails = await connector.fetch_new()
    count = 0
    for raw in raw_emails:
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
                "received_at": raw.received_at.isoformat() if raw.received_at else None,
                "links": raw.links,
                "attachments": raw.attachments,
                "raw": raw.raw,
            }
        )
        count += 1
    return count


def _parse_dt(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        if isinstance(value, datetime):
            return value
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except Exception:  # noqa: BLE001
        return None
