"""English ↔ Hindi translation + romanization helpers."""

from __future__ import annotations

import re
from functools import lru_cache

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from app.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


DEVANAGARI_RE = re.compile(r"[\u0900-\u097F]")


def is_hindi(text: str) -> bool:
    if not text:
        return False
    devanagari = sum(1 for c in text if DEVANAGARI_RE.match(c))
    return devanagari / max(1, len(text)) > 0.15


@lru_cache(maxsize=1)
def _llm() -> ChatOpenAI:
    return ChatOpenAI(
        model=settings.openai_model,
        temperature=0.2,
        api_key=settings.openai_api_key,
    )


async def to_hindi(text: str) -> str:
    """Translate natural English into conversational Hindi (Devanagari)."""
    if not text or is_hindi(text):
        return text
    if not settings.openai_api_key:
        return text  # graceful no-op for local dev without key
    try:
        resp = await _llm.ainvoke(
            [
                SystemMessage(
                    content=(
                        "You translate English to natural spoken Hindi (Devanagari). "
                        "Keep numbers, dates, brands, and proper nouns intact. "
                        "Output ONLY the translation, no commentary."
                    )
                ),
                HumanMessage(content=text),
            ]
        )
        return resp.content.strip()
    except Exception as exc:  # noqa: BLE001
        logger.warning("translation_failed", error=str(exc))
        return text


async def to_hinglish(text: str) -> str:
    if not text or not settings.openai_api_key:
        return text
    resp = await _llm.ainvoke(
        [
            SystemMessage(
                content=(
                    "Convert the English sentence to natural Hinglish (Roman script). "
                    "Keep technical terms in English. Output ONLY the Hinglish version."
                )
            ),
            HumanMessage(content=text),
        ]
    )
    return resp.content.strip()
