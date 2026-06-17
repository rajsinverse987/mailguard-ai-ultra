"""Tests for WhatsApp dispatcher (mocked providers)."""

from __future__ import annotations

import pytest

from app.services.messaging.dispatcher import format_rich_text


def test_format_includes_threat_when_phishing() -> None:
    text = format_rich_text(
        {
            "subject": "Verify your account",
            "sender": "PayPal",
            "summary": "Click here immediately",
            "priority": "high",
            "is_phishing": True,
            "threat_score": 92,
            "action_items": ["Do not click any links"],
        },
        language="en",
    )
    assert "Threat Score" in text
    assert "92" in text


def test_format_includes_deadlines() -> None:
    text = format_rich_text(
        {
            "subject": "Invoice due",
            "sender": "Acme Corp",
            "summary": "Payment due soon",
            "priority": "high",
            "due_dates": ["2026-06-20"],
            "action_items": ["Pay the invoice"],
        },
        language="en",
    )
    assert "Deadline" in text or "2026-06-20" in text
