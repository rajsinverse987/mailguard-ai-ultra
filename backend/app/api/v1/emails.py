"""Email endpoints."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
import re
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, SessionDep
from app.core.logging import get_logger
from app.models.email import Email
from app.models.email_account import EmailAccount
from app.schemas.email import EmailDetailOut, EmailListOut, EmailSummaryOut, ManualEmailIn
from app.services.ai.analyzer import get_analyzer
from app.services.ai.fraud_detector import analyze_threat
from app.services.vector.store import get_vector_store
from app.workers.tasks_email import process_raw_email

router = APIRouter(prefix="/emails", tags=["emails"])
logger = get_logger(__name__)


def _extract_links(text: str) -> list[str]:
    return re.findall(r"https?://[^\s<>)\"']+", text or "")


@router.get("", response_model=EmailListOut)
async def list_emails(
    user: CurrentUser,
    db: SessionDep,
    page: int = Query(1, ge=1),
    size: int = Query(25, ge=1, le=100),
    category: str | None = None,
    priority: str | None = None,
    search: str | None = None,
) -> EmailListOut:
    query = select(Email).where(Email.user_id == user.id)
    if category:
        query = query.where(Email.category == category)
    if priority:
        query = query.where(Email.priority == priority)
    if search:
        query = query.where(Email.subject.ilike(f"%{search}%"))

    total = (
        await db.execute(select(func.count()).select_from(query.subquery()))
    ).scalar_one()

    rows = (
        await db.execute(
            query.order_by(desc(Email.received_at)).offset((page - 1) * size).limit(size)
        )
    ).scalars().all()
    return EmailListOut(
        items=[EmailSummaryOut.model_validate(r) for r in rows],
        total=total or 0,
        page=page,
        size=size,
    )


@router.post("/manual", response_model=EmailDetailOut, status_code=201)
async def create_manual_email(
    payload: ManualEmailIn, user: CurrentUser, db: SessionDep
) -> EmailDetailOut:
    account = (
        await db.execute(
            select(EmailAccount).where(
                EmailAccount.user_id == user.id,
                EmailAccount.provider == "manual",
            )
        )
    ).scalar_one_or_none()
    if not account:
        account = EmailAccount(
            user_id=user.id,
            provider="manual",
            email_address=user.email,
            display_name="Manual test inbox",
            is_active=True,
            extra={"source": "manual"},
        )
        db.add(account)
        await db.flush()

    received_at = payload.received_at or datetime.now(timezone.utc)
    links = _extract_links(payload.body_text)
    analysis = await get_analyzer().analyze(
        subject=payload.subject,
        sender=payload.sender_email,
        body=payload.body_text,
        received_at=received_at,
    )
    threat = await analyze_threat(
        {
            "sender_email": payload.sender_email,
            "sender_name": payload.sender_name,
            "subject": payload.subject,
            "body_text": payload.body_text,
            "links": links,
        }
    )

    email = Email(
        user_id=user.id,
        account_id=account.id,
        provider_message_id=f"manual:{uuid.uuid4()}",
        subject=payload.subject,
        sender_email=str(payload.sender_email),
        sender_name=payload.sender_name,
        sender_company=analysis.get("sender_company"),
        to_recipients=[user.email],
        cc_recipients=[],
        body_text=payload.body_text,
        snippet=payload.body_text[:512] if payload.body_text else payload.subject[:512],
        received_at=received_at,
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
        links=links,
        attachments=[],
        labels=analysis.get("labels", []),
        is_phishing=bool(threat.get("is_phishing")),
        is_spam=bool(threat.get("is_scam")),
        threat_score=float(threat.get("threat_score", 0)),
        threat_reason=threat.get("reasoning"),
        processed=True,
        raw={"analysis": analysis, "threat": threat, "source": "manual"},
    )
    db.add(email)
    await db.flush()

    if threat.get("threat_score", 0) >= 60:
        from app.models.fraud_alert import FraudAlert

        db.add(
            FraudAlert(
                user_id=user.id,
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
        )

    await db.commit()
    await db.refresh(email)

    try:
        await get_vector_store().upsert(
            doc_id=str(email.id),
            text=f"{email.subject}\n\n{email.body_text[:2000]}",
            metadata={
                "user_id": str(user.id),
                "category": email.category,
                "priority": email.priority,
                "subject": email.subject,
                "sender": email.sender_email,
            },
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("manual_email_vector_upsert_failed", email_id=str(email.id), error=str(exc))

    return EmailDetailOut.model_validate(email)


@router.get("/{email_id}", response_model=EmailDetailOut)
async def get_email(email_id: uuid.UUID, user: CurrentUser, db: SessionDep) -> EmailDetailOut:
    e = await db.get(Email, email_id)
    if not e or e.user_id != user.id:
        raise HTTPException(status_code=404, detail="not found")
    return EmailDetailOut.model_validate(e)


@router.get("/semantic/search")
async def semantic_search(
    user: CurrentUser,
    db: SessionDep,
    q: str = Query(..., min_length=2),
    k: int = Query(10, ge=1, le=50),
) -> list[dict[str, Any]]:
    vs = get_vector_store()
    results = await vs.search(q, k=k, filter_={"user_id": str(user.id)})
    enriched: list[dict[str, Any]] = []
    for hit in results:
        try:
            e = await db.get(Email, uuid.UUID(hit["id"]))
            if e and e.user_id == user.id:
                enriched.append(
                    {
                        "email": EmailSummaryOut.model_validate(e).model_dump(mode="json"),
                        "score": hit.get("score"),
                    }
                )
        except Exception:  # noqa: BLE001
            continue
    return enriched
