"""TTS service: OpenAI primary, Google TTS fallback, gTTS offline fallback."""

from __future__ import annotations

import asyncio
import base64
import io
import os
from pathlib import Path
from typing import Any

import httpx

from app.config import settings
from app.core.logging import get_logger
from app.services.voice.voice_styles import pick_voice

logger = get_logger(__name__)


# --- Voice text builder ----------------------------------------------------
class VoiceComposer:
    """Constructs natural spoken-Hindi summaries from email analysis."""

    CRITICAL_PREFIX_HI = "चेतावनी। यह ईमेल अत्यंत महत्वपूर्ण है।"
    BANK_PREFIX_HI = "आपके बैंक खाते से संबंधित नया संदेश प्राप्त हुआ है।"
    INTERVIEW_PREFIX_HI = "बधाई हो। आपको इंटरव्यू निमंत्रण प्राप्त हुआ है।"
    FRAUD_PREFIX_HI = "सावधान। यह ईमेल संदिग्ध प्रतीत होता है।"

    @classmethod
    def compose(
        cls,
        *,
        user_name: str,
        analysis: dict[str, Any],
        language: str = "hi",
    ) -> str:
        category = analysis.get("category", "personal")
        priority = analysis.get("priority", "medium")
        is_phishing = analysis.get("is_phishing") or analysis.get("threat_score", 0) >= 60
        sender = analysis.get("sender_company") or analysis.get("sender_name") or analysis.get("sender")
        subject = analysis.get("subject", "")

        if language == "hi":
            return cls._compose_hi(user_name, category, priority, is_phishing, sender, subject)
        return cls._compose_en(user_name, category, priority, is_phishing, sender, subject)

    @classmethod
    def _compose_hi(
        cls,
        user_name: str,
        category: str,
        priority: str,
        is_phishing: bool,
        sender: str | None,
        subject: str,
    ) -> str:
        greeting = f"नमस्ते {user_name}।" if user_name else "नमस्ते।"
        prefix = ""
        if is_phishing:
            prefix = cls.FRAUD_PREFIX_HI
        elif priority == "critical":
            prefix = cls.CRITICAL_PREFIX_HI
        elif category == "banking":
            prefix = cls.BANK_PREFIX_HI
        elif category == "interview_calls":
            prefix = cls.INTERVIEW_PREFIX_HI

        sender_part = f"{sender} की ओर से" if sender else "एक नया"
        subject_part = subject or "ईमेल"
        closing = "कृपया अपना ईमेल देखें।" if priority in {"high", "critical"} else ""
        parts = [greeting, prefix, f"आपको {sender_part} नया ईमेल प्राप्त हुआ है। विषय है: {subject_part}।"]
        if closing:
            parts.append(closing)
        return " ".join(p for p in parts if p)

    @classmethod
    def _compose_en(
        cls,
        user_name: str,
        category: str,
        priority: str,
        is_phishing: bool,
        sender: str | None,
        subject: str,
    ) -> str:
        greeting = f"Hello {user_name}." if user_name else "Hello."
        prefix = ""
        if is_phishing:
            prefix = "Warning. This email looks suspicious."
        elif priority == "critical":
            prefix = "Attention. This email is extremely important."
        elif category == "banking":
            prefix = "You have a new banking alert."
        elif category == "interview_calls":
            prefix = "Congratulations. You have an interview invitation."

        sender_part = f"from {sender}" if sender else "new"
        subject_part = subject or "email"
        closing = "Please check your inbox." if priority in {"high", "critical"} else ""
        parts = [greeting, prefix, f"You have a {sender_part} email. Subject: {subject_part}."]
        if closing:
            parts.append(closing)
        return " ".join(p for p in parts if p)


# --- TTS engines -----------------------------------------------------------
class TTSService:
    def __init__(self) -> None:
        self.cache_dir = Path(os.getenv("VOICE_CACHE_DIR", "./voice_cache"))
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    async def synthesize(
        self,
        text: str,
        *,
        language: str = "hi",
        voice_key: str = "personal_assistant_female",
        gender: str = "female",
        preferred: str = "personal_assistant",
        priority: str = "medium",
        category: str = "personal",
    ) -> dict[str, Any]:
        if not text.strip():
            raise ValueError("Empty TTS input")

        profile = pick_voice(
            priority, category, preferred=preferred, gender=gender
        )

        # Cache hit
        cache_key = f"{profile.key}_{language}_{hash(text)}"
        cache_path = self.cache_dir / f"{cache_key}.mp3"
        if cache_path.exists():
            return {
                "audio_bytes": cache_path.read_bytes(),
                "mime": "audio/mpeg",
                "voice": profile.key,
                "engine": "cache",
                "duration_ms": None,
            }

        audio: bytes | None = None
        engine = "openai"
        try:
            audio = await self._openai_tts(text, profile.openai_voice)
        except Exception as exc:  # noqa: BLE001
            logger.warning("openai_tts_failed_fallback", error=str(exc))
            engine = "gtts"
            audio = await self._gtts_fallback(text, language)

        cache_path.write_bytes(audio)
        return {
            "audio_bytes": audio,
            "mime": "audio/mpeg",
            "voice": profile.key,
            "engine": engine,
            "duration_ms": None,
        }

    async def _openai_tts(self, text: str, voice: str) -> bytes:
        if not settings.openai_api_key:
            raise RuntimeError("OpenAI key not configured")
        url = "https://api.openai.com/v1/audio/speech"
        headers = {
            "Authorization": f"Bearer {settings.openai_api_key}",
            "Content-Type": "application/json",
        }
        payload = {"model": settings.openai_tts_model, "voice": voice, "input": text}
        async with httpx.AsyncClient(timeout=60) as client:
            r = await client.post(url, headers=headers, json=payload)
            r.raise_for_status()
            return r.content

    async def _gtts_fallback(self, text: str, language: str) -> bytes:
        from gtts import gTTS

        lang = "hi" if language == "hi" else "en"
        tts = gTTS(text=text, lang=lang, slow=False)
        buf = io.BytesIO()
        await asyncio.to_thread(tts.write_to_fp, buf)
        return buf.getvalue()

    @staticmethod
    def to_data_uri(audio: bytes, mime: str = "audio/mpeg") -> str:
        return f"data:{mime};base64,{base64.b64encode(audio).decode()}"


_tts: TTSService | None = None


def get_tts() -> TTSService:
    global _tts
    if _tts is None:
        _tts = TTSService()
    return _tts
