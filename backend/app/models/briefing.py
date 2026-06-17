"""Daily / weekly briefing summaries sent to users."""

from __future__ import annotations

import uuid

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPKMixin


class Briefing(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "briefings"

    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    kind: Mapped[str] = mapped_column(String(16))  # morning | evening | weekly
    period_start: Mapped[str] = mapped_column(String(64))
    period_end: Mapped[str] = mapped_column(String(64))
    language: Mapped[str] = mapped_column(String(8), default="hi")
    text: Mapped[str] = mapped_column(Text)
    stats: Mapped[dict] = mapped_column(JSONB, default=dict)
    voice_note_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), nullable=True
    )
    delivered: Mapped[bool] = mapped_column(Boolean, default=False)
    important_count: Mapped[int] = mapped_column(Integer, default=0)
    total_count: Mapped[int] = mapped_column(Integer, default=0)
