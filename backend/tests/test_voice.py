"""Tests for the TTS service and voice composer."""

from __future__ import annotations

import pytest

from app.services.voice.tts import VoiceComposer
from app.services.voice.voice_styles import pick_voice, VOICE_PROFILES


def test_voice_compose_critical_banking() -> None:
    analysis = {
        "category": "banking",
        "priority": "high",  # use "high" so banking prefix shows (critical takes precedence)
        "is_phishing": False,
        "threat_score": 0,
        "sender_company": "HDFC Bank",
        "subject": "Transaction Alert",
    }
    text = VoiceComposer.compose(user_name="Raj", analysis=analysis, language="hi")
    assert "नमस्ते Raj" in text
    # banking prefix uses "बैंक खाते" (bank account).
    assert "बैंक" in text
    assert "HDFC Bank" in text


def test_voice_compose_interview_hindi() -> None:
    analysis = {
        "category": "interview_calls",
        "priority": "high",
        "sender_company": "Microsoft",
        "subject": "Interview Invitation",
    }
    text = VoiceComposer.compose(user_name="Priya", analysis=analysis, language="hi")
    assert "बधाई" in text or "इंटरव्यू" in text


def test_voice_compose_fraud_alert() -> None:
    analysis = {
        "category": "personal",
        "priority": "medium",
        "is_phishing": True,
        "threat_score": 90,
        "sender_company": "Fake Bank",
        "subject": "Verify now",
    }
    text = VoiceComposer.compose(user_name="Raj", analysis=analysis, language="hi")
    assert "सावधान" in text or "संदिग्ध" in text


def test_voice_compose_english() -> None:
    text = VoiceComposer.compose(
        user_name="Raj",
        analysis={"category": "banking", "priority": "critical", "sender_company": "HDFC"},
        language="en",
    )
    assert "Hello Raj" in text
    assert "HDFC" in text


def test_pick_voice_critical() -> None:
    profile = pick_voice("critical", "personal", preferred="personal_assistant", gender="female")
    assert profile.key == "urgent_alert"


def test_pick_voice_default_female() -> None:
    profile = pick_voice("medium", "personal", preferred="personal_assistant", gender="female")
    assert profile.key == "personal_assistant_female"


def test_pick_voice_default_male() -> None:
    profile = pick_voice("medium", "personal", preferred="personal_assistant", gender="male")
    assert profile.key == "personal_assistant_male"
