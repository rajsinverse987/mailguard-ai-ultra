"""Voice note artifacts stored in object storage."""

from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPKMixin


class VoiceNote(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "voice_notes"

    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    email_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("emails.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    text: Mapped[str] = mapped_column(String(4096))
    text_hi: Mapped[str | None] = mapped_column(String(4096), nullable=True)
    language: Mapped[str] = mapped_column(String(8), default="hi")
    voice: Mapped[str] = mapped_column(String(64), default="personal_assistant")
    gender: Mapped[str] = mapped_column(String(8), default="female")
    engine: Mapped[str] = mapped_column(String(16), default="openai")
    audio_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    storage_key: Mapped[str | None] = mapped_column(String(512), nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    mime: Mapped[str] = mapped_column(String(32), default="audio/mpeg")
