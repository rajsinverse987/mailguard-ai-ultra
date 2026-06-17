"""Auth + user schemas."""

from __future__ import annotations

import uuid

from pydantic import BaseModel, EmailStr, Field

from app.core.security import Role


class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=1, max_length=255)
    phone: str | None = None
    preferred_language: str = "hi"
    preferred_voice: str = "personal_assistant"


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class UserOut(BaseModel):
    id: uuid.UUID
    email: EmailStr
    full_name: str
    phone: str | None
    whatsapp_number: str | None
    role: str
    preferred_language: str
    preferred_voice: str
    voice_gender: str
    morning_briefing_time: str
    enable_voice_alerts: bool
    enable_text_alerts: bool

    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    full_name: str | None = None
    phone: str | None = None
    whatsapp_number: str | None = None
    preferred_language: str | None = None
    preferred_voice: str | None = None
    voice_gender: str | None = None
    morning_briefing_time: str | None = None
    enable_voice_alerts: bool | None = None
    enable_text_alerts: bool | None = None


__all__ = ["Role"]
