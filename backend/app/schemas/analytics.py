"""Analytics schemas."""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel


class CountBucket(BaseModel):
    key: str
    count: int


class TimelineBucket(BaseModel):
    date: date
    count: int


class AnalyticsOverview(BaseModel):
    total_emails: int
    total_important: int
    total_fraud: int
    total_interviews: int
    total_banking: int
    total_unread: int
    voice_notes_sent: int
    whatsapp_sent: int


class AnalyticsResponse(BaseModel):
    overview: AnalyticsOverview
    by_category: list[CountBucket]
    by_priority: list[CountBucket]
    by_sender: list[CountBucket]
    timeline: list[TimelineBucket]
    scam_trend: list[TimelineBucket]
