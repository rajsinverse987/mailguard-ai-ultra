"""End-to-end integration test — analyze → embed → fraud → notify (mocked)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from unittest.mock import patch

import pytest

from app.services.ai.analyzer import AIAnalyzer
from app.services.ai.fraud_detector import analyze_threat
from app.services.messaging.dispatcher import format_rich_text
from app.services.vector.store import VectorStore
from app.services.voice.tts import VoiceComposer


@pytest.mark.asyncio
async def test_full_email_pipeline() -> None:
    # 1. Analyze
    analyzer = AIAnalyzer()
    raw = {
        "subject": "Microsoft Interview Invitation — Senior Engineer",
        "sender_email": "hr@microsoft.com",
        "sender_name": "Microsoft HR",
        "body_text": (
            "Congratulations Raj — you have been shortlisted for the Senior "
            "Software Engineer role. Your interview is scheduled on 20 June 2026 "
            "at 10:00 AM. Please confirm."
        ),
    }
    analysis = await analyzer.analyze(
        subject=raw["subject"],
        sender=raw["sender_email"],
        body=raw["body_text"],
        received_at=datetime.now(timezone.utc),
    )
    assert analysis["priority"] in {"critical", "high", "medium", "low"}

    # 2. Embed + search
    vs = VectorStore(collection_name="integration_test")
    doc_id = f"test-{uuid.uuid4()}"
    text = f"{analysis.get('subject', raw['subject'])}\n\n{raw['body_text'][:2000]}"
    await vs.upsert(
        doc_id=doc_id,
        text=text,
        metadata={"user_id": "test-user", "category": analysis["category"]},
    )
    hits = await vs.search("interview", k=3)
    assert any(doc_id in h.get("id", "") for h in hits) or any(doc_id in str(h.get("metadata", {}).get("id", "")) for h in hits)

    # 3. Fraud
    threat = await analyze_threat(
        {
            "sender_email": raw["sender_email"],
            "sender_name": raw["sender_name"],
            "subject": raw["subject"],
            "body_text": raw["body_text"],
            "links": [],
        }
    )
    assert 0 <= threat["threat_score"] <= 100

    # 4. WhatsApp rich text
    formatted = format_rich_text(
        {
            "subject": raw["subject"],
            "sender": raw["sender_email"],
            "sender_name": raw["sender_name"],
            "sender_company": "Microsoft",
            "summary": analysis.get("summary"),
            "summary_hi": analysis.get("summary_hi"),
            "priority": analysis["priority"],
            "due_dates": analysis.get("due_dates", []),
            "action_items": analysis.get("action_items", []),
            "is_phishing": threat.get("is_phishing"),
            "threat_score": threat["threat_score"],
        },
        language="hi",
    )
    assert "Microsoft" in formatted or "इंटरव्यू" in formatted

    # 5. Voice composer
    voice = VoiceComposer.compose(
        user_name="Raj",
        analysis={
            **analysis,
            "sender_company": "Microsoft",
            "subject": raw["subject"],
        },
        language="hi",
    )
    assert "Raj" in voice or "राज" in voice
    assert "Microsoft" in voice or "इंटरव्यू" in voice


@pytest.mark.asyncio
async def test_phishing_email_full_flow() -> None:
    raw = {
        "subject": "URGENT: Verify your PayPal account now",
        "sender_email": "paypal-security@random-domain.tk",
        "sender_name": "PayPal Support",
        "body_text": (
            "Your PayPal account has been suspended due to suspicious activity. "
            "Click http://bit.ly/fake-paypal immediately to verify your account "
            "or your account will be permanently deleted. Wire transfer fee required."
        ),
        "links": ["http://bit.ly/fake-paypal"],
    }
    analyzer = AIAnalyzer()
    analysis = await analyzer.analyze(
        subject=raw["subject"], sender=raw["sender_email"], body=raw["body_text"]
    )
    threat = await analyze_threat({**raw})

    # Phishing should be flagged with high score
    assert threat["threat_score"] >= 60
    assert threat["is_phishing"] is True
    assert any("display name" in r.lower() or "impersonation" in r.lower()
               or "urgent" in r.lower() for r in threat["reasons"])

    # Voice should mention fraud warning
    voice = VoiceComposer.compose(
        user_name="Raj",
        analysis={
            **analysis,
            "sender_company": "PayPal",
            "is_phishing": True,
            "threat_score": threat["threat_score"],
        },
        language="hi",
    )
    assert "सावधान" in voice or "संदिग्ध" in voice
