"""Voice persona definitions for OpenAI TTS."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class VoiceProfile:
    key: str
    openai_voice: str
    description: str


VOICE_PROFILES: dict[str, VoiceProfile] = {
    "female_news_reader": VoiceProfile("female_news_reader", "nova", "Female news reader tone"),
    "male_news_reader": VoiceProfile("male_news_reader", "onyx", "Male news reader tone"),
    "personal_assistant_female": VoiceProfile(
        "personal_assistant_female", "shimmer", "Warm female personal assistant"
    ),
    "personal_assistant_male": VoiceProfile(
        "personal_assistant_male", "echo", "Calm male personal assistant"
    ),
    "urgent_alert": VoiceProfile("urgent_alert", "onyx", "Serious alert tone"),
}


def pick_voice(priority: str, category: str, *, preferred: str, gender: str) -> VoiceProfile:
    """Auto-select a voice profile based on priority + category."""
    if priority == "critical" or category in {"security", "banking"}:
        return VOICE_PROFILES["urgent_alert"]
    key = (
        "personal_assistant_female"
        if gender == "female"
        else "personal_assistant_male"
    )
    if preferred in VOICE_PROFILES:
        return VOICE_PROFILES[preferred]
    return VOICE_PROFILES[key]
