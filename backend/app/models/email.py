"""Analyzed email record."""

from __future__ import annotations

import uuid

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPKMixin


class Email(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "emails"
    __table_args__ = (
        Index("ix_emails_user_received", "user_id", "received_at"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    account_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("email_accounts.id", ondelete="CASCADE"),
        index=True,
    )

    provider_message_id: Mapped[str] = mapped_column(String(512), index=True)
    thread_id: Mapped[str | None] = mapped_column(String(512), nullable=True, index=True)
    subject: Mapped[str] = mapped_column(String(1024))
    sender_email: Mapped[str] = mapped_column(String(255), index=True)
    sender_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    sender_company: Mapped[str | None] = mapped_column(String(255), nullable=True)
    to_recipients: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    cc_recipients: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)

    body_text: Mapped[str] = mapped_column(Text, default="")
    body_html: Mapped[str | None] = mapped_column(Text, nullable=True)
    snippet: Mapped[str | None] = mapped_column(String(512), nullable=True)

    received_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), index=True)

    # AI classification outputs
    category: Mapped[str] = mapped_column(String(64), default="personal", index=True)
    priority: Mapped[str] = mapped_column(String(16), default="medium", index=True)
    sentiment: Mapped[str] = mapped_column(String(16), default="neutral")
    intent: Mapped[str | None] = mapped_column(String(128), nullable=True)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)

    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    summary_hi: Mapped[str | None] = mapped_column(Text, nullable=True)
    action_items: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)

    due_dates: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    meeting_requests: Mapped[list[dict]] = mapped_column(JSONB, default=list)
    tracking_numbers: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    invoice_amounts: Mapped[list[dict]] = mapped_column(JSONB, default=list)
    otp_codes: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    payment_requests: Mapped[list[dict]] = mapped_column(JSONB, default=list)

    links: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    attachments: Mapped[list[dict]] = mapped_column(JSONB, default=list)
    labels: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)

    # Detection flags
    is_phishing: Mapped[bool] = mapped_column(Boolean, default=False)
    is_spam: Mapped[bool] = mapped_column(Boolean, default=False)
    threat_score: Mapped[float] = mapped_column(Float, default=0.0)
    threat_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    processed: Mapped[bool] = mapped_column(Boolean, default=False)
    notified: Mapped[bool] = mapped_column(Boolean, default=False)
    raw: Mapped[dict] = mapped_column(JSONB, default=dict)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Email {self.subject[:40]} priority={self.priority}>"
