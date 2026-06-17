"""Tests for the AI analyzer."""

from __future__ import annotations

import pytest

from app.services.ai.analyzer import AIAnalyzer


@pytest.mark.asyncio
async def test_analyzer_returns_valid_structure() -> None:
    analyzer = AIAnalyzer()
    result = await analyzer.analyze(
        subject="Interview Invitation from Microsoft HR",
        sender="hr@microsoft.com",
        body=(
            "Dear candidate, you are invited to an interview on 20 June 2026 "
            "at 10:00 AM. Please confirm your attendance."
        ),
    )
    assert "category" in result
    assert result["category"] in {
        "banking", "finance", "bills", "orders", "government", "legal",
        "healthcare", "personal", "security", "education", "job_alerts",
        "interview_calls", "travel", "shopping", "investment", "other",
    }
    assert result["priority"] in {"critical", "high", "medium", "low"}
    assert isinstance(result["confidence"], float)
    assert 0 <= result["confidence"] <= 100
    assert isinstance(result.get("summary", ""), str)


@pytest.mark.asyncio
async def test_analyzer_handles_otp_email() -> None:
    analyzer = AIAnalyzer()
    result = await analyzer.analyze(
        subject="Your verification code is 482931",
        sender="no-reply@accounts.google.com",
        body="Your one-time password is 482931. Do not share it.",
    )
    # Mock LLM should still detect OTP via keyword fallback
    assert result["category"] == "security"
    assert result["priority"] in {"critical", "high"}


@pytest.mark.asyncio
async def test_analyzer_handles_empty_body() -> None:
    analyzer = AIAnalyzer()
    result = await analyzer.analyze(
        subject="Test", sender="x@example.com", body=""
    )
    assert result["category"]
    assert result["priority"]
