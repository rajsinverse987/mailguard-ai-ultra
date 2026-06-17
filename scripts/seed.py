"""Seed script — creates a demo user and a few fake emails for development."""

from __future__ import annotations

import asyncio
import os
import uuid
from datetime import datetime, timedelta, timezone

os.environ.setdefault("APP_ENV", "development")
os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+asyncpg://mailguard:mailguard@localhost:5432/mailguard",
)

from sqlalchemy import select  # noqa: E402

from app.core.security import hash_password  # noqa: E402
from app.db.session import SessionLocal  # noqa: E402
from app.models.email import Email  # noqa: E402
from app.models.email_account import EmailAccount  # noqa: E402
from app.models.user import User  # noqa: E402


async def main() -> None:
    async with SessionLocal() as db:
        user = (await db.execute(select(User).where(User.email == "demo@mailguard.ai"))).scalar_one_or_none()
        if not user:
            user = User(
                id=uuid.uuid4(),
                email="demo@mailguard.ai",
                full_name="Demo User",
                hashed_password=hash_password("demo-password"),
                phone="+919999999999",
                whatsapp_number="+919999999999",
                preferred_language="hi",
                preferred_voice="personal_assistant",
                voice_gender="female",
                morning_briefing_time="08:00",
                enable_voice_alerts=True,
                enable_text_alerts=True,
                is_active=True,
                role="admin",
            )
            db.add(user)
            await db.flush()

        acc = (
            await db.execute(
                select(EmailAccount).where(
                    EmailAccount.user_id == user.id, EmailAccount.provider == "gmail"
                )
            )
        ).scalar_one_or_none()
        if not acc:
            acc = EmailAccount(
                id=uuid.uuid4(),
                user_id=user.id,
                provider="gmail",
                email_address="demo@gmail.com",
                display_name="Demo",
                is_active=True,
            )
            db.add(acc)
            await db.flush()

        # Seed a couple of demo emails (no provider_message_id collision risk).
        demo_emails = [
            {
                "subject": "Interview Invitation — Microsoft",
                "sender_email": "hr@microsoft.com",
                "sender_name": "Microsoft HR",
                "sender_company": "Microsoft",
                "category": "interview_calls",
                "priority": "critical",
                "summary": "You have been invited to an interview on 20 June 2026.",
                "summary_hi": "आपको 20 जून 2026 को इंटरव्यू के लिए आमंत्रित किया गया है।",
                "received_at": datetime.now(timezone.utc) - timedelta(hours=2),
                "due_dates": ["2026-06-20"],
                "action_items": ["Confirm your attendance"],
                "threat_score": 0.0,
                "is_phishing": False,
            },
            {
                "subject": "URGENT: Verify your PayPal account",
                "sender_email": "paypal-security@random-domain.tk",
                "sender_name": "PayPal Support",
                "sender_company": "PayPal",
                "category": "security",
                "priority": "high",
                "summary": "Suspicious email requesting immediate verification.",
                "summary_hi": "संदिग्ध ईमेल — तुरंत सत्यापन का अनुरोध।",
                "received_at": datetime.now(timezone.utc) - timedelta(hours=5),
                "is_phishing": True,
                "threat_score": 92.0,
                "threat_reason": "Sender domain does not match PayPal; urgent language detected.",
                "links": ["http://bit.ly/fake-paypal"],
            },
            {
                "subject": "HDFC Bank Statement — May 2026",
                "sender_email": "alerts@hdfcbank.com",
                "sender_name": "HDFC Bank",
                "sender_company": "HDFC Bank",
                "category": "banking",
                "priority": "high",
                "summary": "Your monthly statement is ready.",
                "summary_hi": "आपका मासिक विवरण तैयार है।",
                "received_at": datetime.now(timezone.utc) - timedelta(days=1),
                "action_items": ["Review statement"],
                "threat_score": 0.0,
                "is_phishing": False,
            },
        ]
        for d in demo_emails:
            e = Email(
                id=uuid.uuid4(),
                user_id=user.id,
                account_id=acc.id,
                provider_message_id=f"demo-{uuid.uuid4().hex[:12]}",
                body_text="(demo content)",
                snippet=d["summary"],
                to_recipients=["demo@gmail.com"],
                received_at=d["received_at"],
                processed=True,
                notified=False,
                confidence=85.0,
                sentiment="neutral",
                **{k: v for k, v in d.items() if k not in {"received_at"}},
            )
            db.add(e)
        await db.commit()
        print(f"Seeded demo user {user.email} with {len(demo_emails)} emails.")


if __name__ == "__main__":
    asyncio.run(main())
