"""User account model."""

from __future__ import annotations

import uuid

from sqlalchemy import Boolean, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.security import Role
from app.db.base import Base, TimestampMixin, UUIDPKMixin


class User(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(255))
    hashed_password: Mapped[str] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(String(32), index=True, nullable=True)
    whatsapp_number: Mapped[str | None] = mapped_column(String(32), nullable=True)
    role: Mapped[str] = mapped_column(String(32), default=Role.USER, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    preferred_language: Mapped[str] = mapped_column(String(8), default="hi")
    preferred_voice: Mapped[str] = mapped_column(String(32), default="personal_assistant")
    voice_gender: Mapped[str] = mapped_column(String(8), default="female")
    morning_briefing_time: Mapped[str] = mapped_column(String(8), default="08:00")
    enable_voice_alerts: Mapped[bool] = mapped_column(Boolean, default=True)
    enable_text_alerts: Mapped[bool] = mapped_column(Boolean, default=True)
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), index=True, nullable=True
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<User {self.email} ({self.role})>"
