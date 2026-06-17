"""Email account schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class EmailAccountOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    provider: str
    email_address: str
    display_name: str | None
    is_active: bool
    last_sync_at: str | None
    created_at: datetime


class OAuthStartOut(BaseModel):
    authorize_url: str
    state: str


class OAuthCallbackIn(BaseModel):
    code: str
    state: str
