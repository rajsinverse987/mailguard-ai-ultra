"""Tests for translator helper."""

from __future__ import annotations

from app.services.ai.translator import is_hindi


def test_is_hindi_detects_devanagari() -> None:
    assert is_hindi("नमस्ते दोस्त") is True
    assert is_hindi("Hello, how are you?") is False
    assert is_hindi("") is False


def test_is_hindi_mixed() -> None:
    # Mostly English → False
    long_english = "This is mostly English with one नमस्ते and the rest is English words here for sure ok"
    assert is_hindi(long_english) is False
    # Mostly Hindi → True
    long_hindi = "नमस्ते दोस्त, आप कैसे हैं, मैं ठीक हूँ, और आज का दिन बहुत अच्छा है।"
    assert is_hindi(long_hindi) is True
