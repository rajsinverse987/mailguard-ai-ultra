"""Persisted fraud / phishing detections."""

from __future__ import annotations

import uuid

from sqlalchemy import Boolean, Float, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPKMixin


class FraudAlert(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "fraud_alerts"
    __table_args__ = (Index("ix_fraud_user_created", "user_id", "created_at"),)

    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    email_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("emails.id", ondelete="CASCADE"),
        index=True,
    )
    threat_score: Mapped[float] = mapped_column(Float, default=0.0)
    severity: Mapped[str] = mapped_column(String(16), default="low")
    is_phishing: Mapped[bool] = mapped_column(Boolean, default=False)
    is_scam: Mapped[bool] = mapped_column(Boolean, default=False)
    reasons: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    suspicious_links: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    indicators: Mapped[dict] = mapped_column(JSONB, default=dict)
    reasoning: Mapped[str | None] = mapped_column(Text, nullable=True)
    acknowledged: Mapped[bool] = mapped_column(Boolean, default=False)
