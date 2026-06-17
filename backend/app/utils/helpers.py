"""Misc utility helpers."""

from __future__ import annotations

import re
from typing import Iterable


def normalize_phone(number: str | None) -> str | None:
    """Normalize to E.164-ish format expected by WhatsApp (digits only with optional +)."""
    if not number:
        return None
    digits = re.sub(r"[^\d+]", "", number)
    if not digits.startswith("+"):
        # Default to India if 10 digits
        if len(digits) == 10:
            digits = "+91" + digits
        elif len(digits) == 12 and digits.startswith("91"):
            digits = "+" + digits
        elif len(digits) == 11 and digits.startswith("1"):
            digits = "+" + digits
    return digits


def chunked(iterable: Iterable, size: int):
    buf: list = []
    for item in iterable:
        buf.append(item)
        if len(buf) >= size:
            yield buf
            buf = []
    if buf:
        yield buf


def truncate(text: str, limit: int = 4000) -> str:
    return text[:limit] if text else text
