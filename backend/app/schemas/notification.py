"""Notification schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class NotificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    channel: str
    status: str
    provider: str
    to_number: str
    delivered: bool
    error: str | None
    created_at: datetime
    email_id: uuid.UUID | None


class VoiceNoteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    text: str
    text_hi: str | None
    language: str
    voice: str
    gender: str
    engine: str
    audio_url: str | None
    duration_ms: int | None
    mime: str
    created_at: datetime
