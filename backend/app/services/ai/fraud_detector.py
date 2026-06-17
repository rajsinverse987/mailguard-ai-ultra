"""Phishing + fraud detection using heuristics + LLM reasoning."""

from __future__ import annotations

import json
import re
from typing import Any

import httpx
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.config import settings
from app.core.logging import get_logger
from app.services.ai.prompts import FRAUD_SYSTEM_PROMPT, FRAUD_USER_PROMPT

logger = get_logger(__name__)


# --- Heuristic signals ------------------------------------------------------
URGENT_KEYWORDS = {
    "act now",
    "immediate action",
    "verify your account",
    "suspended",
    "click here",
    "limited time",
    "confirm identity",
    "final notice",
    "unauthorized access",
    "urgent",
    "expires today",
    "wire transfer",
    "gift card",
    "tax refund",
    "social security",
    "bitcoin",
}

SUSPICIOUS_TLDS = {".zip", ".mov", ".country", ".kim", ".work", ".click", ".loan"}
LEGIT_BRANDS = {
    "google": ["google.com", "gmail.com", "googlemail.com"],
    "microsoft": ["microsoft.com", "outlook.com", "office.com", "live.com"],
    "apple": ["apple.com", "icloud.com"],
    "amazon": ["amazon.com", "amazon.in"],
    "paypal": ["paypal.com"],
    "netflix": ["netflix.com"],
    "uber": ["uber.com"],
}


def _extract_domain(email_or_url: str) -> str:
    s = email_or_url.strip().lower()
    if "@" in s:
        return s.split("@", 1)[1]
    m = re.search(r"https?://([^/]+)", s)
    return m.group(1) if m else s


def _is_display_name_mismatch(sender: str) -> bool:
    # e.g. "PayPal Support <paypa1@gmail.com>"
    match = re.search(r"<([^>]+)>", sender)
    if not match:
        return False
    addr = match.group(1)
    domain = _extract_domain(addr)
    display = sender.split("<", 1)[0].lower()
    for brand, allowed in LEGIT_BRANDS.items():
        if brand in display and not any(d in domain for d in allowed):
            return True
    return False


def heuristic_score(email: dict[str, Any]) -> tuple[int, list[str]]:
    """Return (score 0-100, list of reasons)."""
    score = 0
    reasons: list[str] = []

    sender = email.get("sender_email", "") or ""
    sender_display = email.get("sender_name", "") or sender
    subject = (email.get("subject") or "").lower()
    body = (email.get("body_text") or "").lower()
    links = email.get("links") or []

    # Display-name mismatch
    if _is_display_name_mismatch(sender_display):
        score += 30
        reasons.append("Sender display name does not match the actual email domain.")

    # Urgent / action language
    urgent_hits = sum(1 for k in URGENT_KEYWORDS if k in body or k in subject)
    if urgent_hits:
        score += min(20, urgent_hits * 6)
        reasons.append(f"Uses urgent / coercive language ({urgent_hits} signals).")

    # Suspicious TLDs in links
    bad_links = [l for l in links if any(l.lower().endswith(tld) for tld in SUSPICIOUS_TLDS)]
    if bad_links:
        score += 15
        reasons.append(f"Links use uncommon TLDs: {bad_links[:3]}")

    # URL mismatch: visible text vs href
    for l in links:
        if re.search(r"\d{1,3}(\.\d{1,3}){3}", l):  # raw IP address
            score += 25
            reasons.append("Link points to a raw IP address.")

    # Credential request
    if any(
        k in body
        for k in (
            "password",
            "verify your account",
            "reset your password",
            "login here",
            "confirm credentials",
        )
    ):
        score += 15
        reasons.append("Requests credentials or account verification.")

    # Payment request outside known providers
    if "wire" in body or "gift card" in body or "bitcoin" in body or "crypto" in body:
        score += 25
        reasons.append("Unusual payment method requested (wire, gift card, crypto).")

    # Brand impersonation attempt
    for brand, allowed in LEGIT_BRANDS.items():
        if brand in (subject + " " + body):
            sender_domain = _extract_domain(sender)
            if sender_domain and not any(d in sender_domain for d in allowed):
                if brand in sender_display.lower():
                    score += 20
                    reasons.append(
                        f"Possibly impersonates {brand} from an unrelated domain."
                    )

    # Cap
    score = max(0, min(100, score))
    return score, reasons


@retry(
    retry=retry_if_exception_type(Exception),
    wait=wait_exponential(multiplier=1, min=1, max=8),
    stop=stop_after_attempt(3),
    reraise=True,
)
async def _llm_reason(email: dict[str, Any], base_score: int, reasons: list[str]) -> dict[str, Any]:
    if not settings.openai_api_key:
        return _heuristic_only_result(base_score, reasons)

    llm = ChatOpenAI(
        model=settings.openai_model,
        temperature=0.0,
        api_key=settings.openai_api_key,
        model_kwargs={"response_format": {"type": "json_object"}},
    )
    prompt = FRAUD_USER_PROMPT.format(
        sender=email.get("sender_email", ""),
        subject=email.get("subject", ""),
        links=", ".join(email.get("links") or []),
        body=(email.get("body_text") or "")[:4000],
    )
    resp = await llm.ainvoke(
        [SystemMessage(content=FRAUD_SYSTEM_PROMPT), HumanMessage(content=prompt)]
    )
    try:
        return json.loads(resp.content)
    except json.JSONDecodeError:
        match = re.search(r"\{[\s\S]*\}", resp.content)
        return json.loads(match.group(0)) if match else _heuristic_only_result(base_score, reasons)


def _heuristic_only_result(score: int, reasons: list[str]) -> dict[str, Any]:
    return {
        "threat_score": score,
        "severity": (
            "critical" if score >= 85 else "high" if score >= 60 else "medium" if score >= 30 else "low"
        ),
        "is_phishing": score >= 60,
        "is_scam": score >= 50,
        "reasons": reasons,
        "suspicious_links": [],
        "indicators": {},
        "reasoning": "Heuristic-only analysis (no LLM available).",
    }


async def analyze_threat(email: dict[str, Any]) -> dict[str, Any]:
    """Run heuristics + LLM reasoning and return a fraud assessment."""
    base, reasons = heuristic_score(email)
    enriched = await _llm_reason(email, base, reasons)
    # Merge: keep max score
    enriched["threat_score"] = max(base, int(enriched.get("threat_score", base)))
    merged_reasons = list(dict.fromkeys(reasons + (enriched.get("reasons") or [])))
    enriched["reasons"] = merged_reasons
    if "severity" not in enriched or not enriched["severity"]:
        enriched["severity"] = (
            "critical"
            if enriched["threat_score"] >= 85
            else "high"
            if enriched["threat_score"] >= 60
            else "medium"
            if enriched["threat_score"] >= 30
            else "low"
        )
    enriched.setdefault("reasoning", "Combined heuristic + LLM analysis.")
    return enriched
