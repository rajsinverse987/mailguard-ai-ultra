"""Tests for fraud detection heuristics + LLM enrichment."""

from __future__ import annotations

import pytest

from app.services.ai.fraud_detector import (
    _is_display_name_mismatch,
    heuristic_score,
    analyze_threat,
)


@pytest.mark.asyncio
async def test_brand_impersonation_is_flagged() -> None:
    email = {
        "sender_email": "paypal-security@random-domain.tk",
        "sender_name": "PayPal Support",
        "subject": "URGENT: Verify your PayPal account now!",
        "body_text": (
            "Your account has been suspended. Click here immediately to "
            "verify your credentials and restore access. Wire transfer fee "
            "required. http://bit.ly/fake-paypal"
        ),
        "links": ["http://bit.ly/fake-paypal", "http://random-domain.tk/login"],
    }
    result = await analyze_threat(email)
    assert result["threat_score"] >= 60
    assert result["is_phishing"] is True
    assert any("impersonation" in r.lower() or "display name" in r.lower()
               or "urgent" in r.lower() for r in result["reasons"])


def test_display_name_mismatch_paypal_from_gmail() -> None:
    assert _is_display_name_mismatch("PayPal Support <paypa1@gmail.com>") is True


def test_display_name_mismatch_legit() -> None:
    assert _is_display_name_mismatch("PayPal <service@paypal.com>") is False


@pytest.mark.asyncio
async def test_clean_email_is_low_risk() -> None:
    email = {
        "sender_email": "alice@example.com",
        "sender_name": "Alice",
        "subject": "Lunch next week?",
        "body_text": "Hey, want to grab lunch next Tuesday?",
        "links": [],
    }
    result = await analyze_threat(email)
    assert result["threat_score"] < 30
    assert result["is_phishing"] is False
