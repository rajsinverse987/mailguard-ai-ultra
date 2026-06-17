"""Email + analysis schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class EmailSummaryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    subject: str
    sender_email: str
    sender_name: str | None
    sender_company: str | None
    snippet: str | None
    category: str
    priority: str
    sentiment: str
    intent: str | None
    confidence: float
    summary: str | None
    summary_hi: str | None
    action_items: list[str]
    due_dates: list[str]
    is_phishing: bool
    is_spam: bool
    threat_score: float
    threat_reason: str | None
    received_at: datetime
    notified: bool


class EmailDetailOut(EmailSummaryOut):
    body_text: str
    body_html: str | None
    to_recipients: list[str]
    cc_recipients: list[str]
    tracking_numbers: list[str]
    invoice_amounts: list[dict]
    otp_codes: list[str]
    payment_requests: list[dict]
    meeting_requests: list[dict]
    links: list[str]
    attachments: list[dict]
    labels: list[str]


class EmailListOut(BaseModel):
    items: list[EmailSummaryOut]
    total: int
    page: int
    size: int


class ManualEmailIn(BaseModel):
    subject: str = Field(min_length=1, max_length=1024)
    sender_email: EmailStr
    sender_name: str | None = Field(default=None, max_length=255)
    body_text: str = Field(default="", max_length=50000)
    received_at: datetime | None = None


class EmailFilter(BaseModel):
    category: str | None = None
    priority: str | None = None
    sender: str | None = None
    search: str | None = None
    is_phishing: bool | None = None
    from_date: datetime | None = None
    to_date: datetime | None = None


class AnalysisRequest(BaseModel):
    email_id: uuid.UUID


class ChatIn(BaseModel):
    query: str = Field(min_length=1, max_length=1000)
    language: str | None = None
    voice_reply: bool = False


class ChatOut(BaseModel):
    query: str
    answer: str
    answer_hi: str | None = None
    cited_emails: list[EmailSummaryOut] = []
    voice_note_id: uuid.UUID | None = None
