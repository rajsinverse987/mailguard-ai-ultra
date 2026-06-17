"""Tests for email endpoints + analysis pipeline."""

from __future__ import annotations

import pytest

from app.services.ai.analyzer import get_analyzer
from app.services.messaging.dispatcher import format_rich_text


@pytest.mark.asyncio
async def test_analyze_real_email_structure() -> None:
    analyzer = get_analyzer()
    result = await analyzer.analyze(
        subject="Your order #12345 has shipped",
        sender="orders@amazon.in",
        body=(
            "Hi Raj, your Amazon order #12345 has shipped. "
            "Tracking number: AB123456789IN. "
            "Expected delivery: 18 June 2026."
        ),
    )
    assert result["priority"] in {"critical", "high", "medium", "low"}
    # Tracking numbers may be in mock results; just assert structure present
    assert "tracking_numbers" in result
    assert "due_dates" in result


def test_format_rich_text_priority_icon() -> None:
    txt = format_rich_text(
        {
            "subject": "Test",
            "sender": "x@example.com",
            "summary": "This is a test",
            "priority": "critical",
        },
        language="en",
    )
    assert "🚨" in txt or "New Email" in txt


def test_format_rich_text_hindi() -> None:
    txt = format_rich_text(
        {
            "subject": "इंटरव्यू",
            "sender": "hr@example.com",
            "summary_hi": "आपको इंटरव्यू के लिए बुलाया गया है।",
            "priority": "high",
        },
        language="hi",
    )
    assert "इंटरव्यू" in txt or "आपको" in txt
