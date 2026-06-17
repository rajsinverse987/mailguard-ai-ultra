"""Daily / evening briefing generator."""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.briefing import Briefing
from app.models.email import Email
from app.models.user import User
from app.services.ai.translator import to_hindi

logger = get_logger(__name__)


def _bucket_count(items: list, key: str, value: Any) -> int:
    return sum(1 for x in items if x.get(key) == value)


def _top_senders(emails: list[dict[str, Any]], k: int = 5) -> list[str]:
    counts: dict[str, int] = {}
    for e in emails:
        s = e.get("sender_email") or "unknown"
        counts[s] = counts.get(s, 0) + 1
    return [s for s, _ in sorted(counts.items(), key=lambda x: -x[1])[:k]]


def compose_morning_text(user: User, stats: dict[str, Any]) -> str:
    today = stats.get("date", date.today().isoformat())
    return (
        f"सुप्रभात {user.full_name.split(' ')[0]}. "
        f"कल {today} को आपको {stats['total']} ईमेल प्राप्त हुए। "
        f"उनमें से {stats['important']} महत्वपूर्ण थे, "
        f"{stats['job_count']} नौकरी से संबंधित थे, "
        f"{stats['bank_count']} बैंकिंग अलर्ट थे, "
        f"{stats['interview_count']} इंटरव्यू निमंत्रण थे, "
        f"और {stats['phishing_count']} संदिग्ध ईमेल पकड़े गए। "
        f"कृपया अपना मेलगार्ड डैशबोर्ड देखें।"
    )


def compose_evening_text(user: User, stats: dict[str, Any]) -> str:
    return (
        f"शुभ संध्या {user.full_name.split(' ')[0]}. "
        f"आज आपने {stats['total']} ईमेल देखे। "
        f"{stats['important']} महत्वपूर्ण थे। "
        f"{stats['pending_actions']} कार्य लंबित हैं। "
        f"{stats['missed_deadlines']} समय-सीमा समाप्त हो चुकी है। "
        f"{stats['upcoming_meetings']} मीटिंग कल होनी है। "
        f"अपना मेलगार्ड डैशबोर्ड देखें।"
    )


async def generate_morning_briefing(
    db: AsyncSession, user: User, *, day: date | None = None
) -> Briefing:
    day = day or date.today()
    start = datetime.combine(day - timedelta(days=1), datetime.min.time(), tzinfo=timezone.utc)
    end = datetime.combine(day, datetime.min.time(), tzinfo=timezone.utc)

    result = await db.execute(
        select(Email).where(
            Email.user_id == user.id,
            Email.received_at >= start,
            Email.received_at < end,
        )
    )
    emails = result.scalars().all()
    email_dicts = [_email_to_dict(e) for e in emails]

    stats = {
        "date": day.isoformat(),
        "total": len(emails),
        "important": sum(1 for e in emails if e.priority in {"high", "critical"}),
        "job_count": sum(1 for e in emails if e.category == "job_alerts"),
        "bank_count": sum(1 for e in emails if e.category == "banking"),
        "interview_count": sum(1 for e in emails if e.category == "interview_calls"),
        "bills_count": sum(1 for e in emails if e.category == "bills"),
        "phishing_count": sum(1 for e in emails if e.is_phishing),
        "top_senders": _top_senders(email_dicts),
    }

    text_hi = compose_morning_text(user, stats)
    if user.preferred_language == "en":
        text_en = await to_hindi(text_hi)  # placeholder, will be translated later
    else:
        text_en = text_hi

    briefing = Briefing(
        user_id=user.id,
        kind="morning",
        period_start=start.isoformat(),
        period_end=end.isoformat(),
        language=user.preferred_language or "hi",
        text=text_hi,
        stats=stats,
        important_count=stats["important"],
        total_count=stats["total"],
    )
    db.add(briefing)
    await db.flush()
    return briefing


async def generate_evening_briefing(
    db: AsyncSession, user: User, *, day: date | None = None
) -> Briefing:
    day = day or date.today()
    start = datetime.combine(day, datetime.min.time(), tzinfo=timezone.utc)
    end = datetime.combine(day + timedelta(days=1), datetime.min.time(), tzinfo=timezone.utc)
    result = await db.execute(
        select(Email).where(
            Email.user_id == user.id,
            Email.received_at >= start,
            Email.received_at < end,
        )
    )
    emails = result.scalars().all()
    stats = {
        "total": len(emails),
        "important": sum(1 for e in emails if e.priority in {"high", "critical"}),
        "pending_actions": sum(len(e.action_items) for e in emails),
        "missed_deadlines": sum(1 for e in emails if e.priority == "critical"),
        "upcoming_meetings": sum(1 for e in emails if e.meeting_requests),
    }
    text_hi = compose_evening_text(user, stats)
    briefing = Briefing(
        user_id=user.id,
        kind="evening",
        period_start=start.isoformat(),
        period_end=end.isoformat(),
        language=user.preferred_language or "hi",
        text=text_hi,
        stats=stats,
        important_count=stats["important"],
        total_count=stats["total"],
    )
    db.add(briefing)
    await db.flush()
    return briefing


def _email_to_dict(e: Email) -> dict[str, Any]:
    return {
        "subject": e.subject,
        "sender_email": e.sender_email,
        "sender_company": e.sender_company,
        "category": e.category,
        "priority": e.priority,
        "due_dates": list(e.due_dates or []),
        "invoice_amounts": list(e.invoice_amounts or []),
    }
