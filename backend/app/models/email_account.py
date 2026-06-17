"""Connected mailbox accounts (Gmail, Outlook)."""

from __future__ import annotations

import uuid

from sqlalchemy import Boolean, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPKMixin


class EmailAccount(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "email_accounts"
    __table_args__ = (
        UniqueConstraint("user_id", "provider", "email_address", name="uq_account_user"),
        Index("ix_account_user_provider", "user_id", "provider"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    provider: Mapped[str] = mapped_column(String(16))  # gmail | outlook
    email_address: Mapped[str] = mapped_column(String(255), index=True)
    display_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Tokens are stored AES-GCM encrypted
    access_token: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    refresh_token: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    token_expires_at: Mapped[str | None] = mapped_column(String(64), nullable=True)
    scope: Mapped[str | None] = mapped_column(String(1024), nullable=True)

    history_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    watch_expiration: Mapped[str | None] = mapped_column(String(64), nullable=True)
    subscription_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_sync_at: Mapped[str | None] = mapped_column(String(64), nullable=True)
    extra: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
