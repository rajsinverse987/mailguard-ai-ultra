"""Analytics endpoints."""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, SessionDep
from app.models.email import Email
from app.models.notification import Notification
from app.models.voice_note import VoiceNote
from app.schemas.analytics import (
    AnalyticsOverview,
    AnalyticsResponse,
    CountBucket,
    TimelineBucket,
)

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/overview", response_model=AnalyticsResponse)
async def overview(user: CurrentUser, db: SessionDep) -> AnalyticsResponse:
    now = datetime.now(timezone.utc)
    since_30 = now - timedelta(days=30)

    total = (
        await db.execute(
            select(func.count()).select_from(Email).where(Email.user_id == user.id)
        )
    ).scalar_one() or 0

    important = (
        await db.execute(
            select(func.count())
            .select_from(Email)
            .where(Email.user_id == user.id, Email.priority.in_(["high", "critical"]))
        )
    ).scalar_one() or 0

    fraud = (
        await db.execute(
            select(func.count())
            .select_from(Email)
            .where(Email.user_id == user.id, Email.is_phishing.is_(True))
        )
    ).scalar_one() or 0

    interviews = (
        await db.execute(
            select(func.count())
            .select_from(Email)
            .where(Email.user_id == user.id, Email.category == "interview_calls")
        )
    ).scalar_one() or 0

    banking = (
        await db.execute(
            select(func.count())
            .select_from(Email)
            .where(Email.user_id == user.id, Email.category == "banking")
        )
    ).scalar_one() or 0

    unread = (
        await db.execute(
            select(func.count())
            .select_from(Email)
            .where(Email.user_id == user.id, Email.notified.is_(False))
        )
    ).scalar_one() or 0

    voice_count = (
        await db.execute(
            select(func.count())
            .select_from(VoiceNote)
            .where(VoiceNote.user_id == user.id)
        )
    ).scalar_one() or 0

    whatsapp_count = (
        await db.execute(
            select(func.count())
            .select_from(Notification)
            .where(Notification.user_id == user.id)
        )
    ).scalar_one() or 0

    # Distribution queries
    by_cat_q = (
        await db.execute(
            select(Email.category, func.count())
            .where(Email.user_id == user.id)
            .group_by(Email.category)
        )
    ).all()
    by_priority_q = (
        await db.execute(
            select(Email.priority, func.count())
            .where(Email.user_id == user.id)
            .group_by(Email.priority)
        )
    ).all()
    by_sender_q = (
        await db.execute(
            select(Email.sender_email, func.count())
            .where(Email.user_id == user.id)
            .group_by(Email.sender_email)
            .order_by(func.count().desc())
            .limit(10)
        )
    ).all()

    # Timeline
    rows = (
        await db.execute(
            select(Email.received_at, Email.is_phishing)
            .where(Email.user_id == user.id, Email.received_at >= since_30)
        )
    ).all()
    daily: Counter = Counter()
    scam_daily: Counter = Counter()
    for r in rows:
        d = r[0].date().isoformat()
        daily[d] += 1
        if r[1]:
            scam_daily[d] += 1

    return AnalyticsResponse(
        overview=AnalyticsOverview(
            total_emails=total,
            total_important=important,
            total_fraud=fraud,
            total_interviews=interviews,
            total_banking=banking,
            total_unread=unread,
            voice_notes_sent=voice_count,
            whatsapp_sent=whatsapp_count,
        ),
        by_category=[CountBucket(key=k or "other", count=v) for k, v in by_cat_q],
        by_priority=[CountBucket(key=k or "medium", count=v) for k, v in by_priority_q],
        by_sender=[CountBucket(key=k or "unknown", count=v) for k, v in by_sender_q],
        timeline=[TimelineBucket(date=date.fromisoformat(d), count=c) for d, c in sorted(daily.items())],
        scam_trend=[TimelineBucket(date=date.fromisoformat(d), count=c) for d, c in sorted(scam_daily.items())],
    )
