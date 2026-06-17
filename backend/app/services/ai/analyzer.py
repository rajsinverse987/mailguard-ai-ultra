"""Main AI analyzer — orchestrates LLM calls and produces structured analysis."""

from __future__ import annotations

import json
import re
from datetime import datetime
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
from app.services.ai.prompts import (
    ANALYSIS_SYSTEM_PROMPT,
    ANALYSIS_USER_PROMPT,
    CATEGORIES,
)

logger = get_logger(__name__)


def _strip_json(text: str) -> dict[str, Any]:
    """Extract JSON from a model response even if it has stray commentary."""
    if not text:
        return {}
    cleaned = text.strip()
    # Strip ```json fences
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    # Find the first { ... last }
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"\{[\s\S]*\}", cleaned)
        if match:
            return json.loads(match.group(0))
        raise


@retry(
    retry=retry_if_exception_type(Exception),
    wait=wait_exponential(multiplier=1, min=1, max=8),
    stop=stop_after_attempt(3),
    reraise=True,
)
async def _call_llm(messages: list[Any]) -> str:
    if not settings.openai_api_key:
        # Local deterministic mock so dev environments work without a key.
        return _mock_analysis(messages[-1].content if messages else "")
    llm = ChatOpenAI(
        model=settings.openai_model,
        temperature=0.1,
        api_key=settings.openai_api_key,
        model_kwargs={"response_format": {"type": "json_object"}},
    )
    resp = await llm.ainvoke([SystemMessage(content=messages[0]), HumanMessage(content=messages[1])])
    return resp.content


def _mock_analysis(user_prompt: str) -> str:
    """Cheap offline fallback so dev environments without API keys still work."""
    subject_match = re.search(r"Subject:\s*(.+)", user_prompt)
    subject = subject_match.group(1).strip() if subject_match else "Email"
    body_match = re.search(
        r"Email body:\s*\"\"\"\s*([\s\S]*?)\s*\"\"\"",
        user_prompt,
    )
    body = body_match.group(1).strip() if body_match else ""

    lower = f"{subject}\n{body}".lower()
    if any(k in lower for k in ("otp", "one time", "one-time", "verification code")):
        category, priority, intent = "security", "high", "OTP delivery"
    elif any(k in lower for k in ("interview", "assessment", "hiring")):
        category, priority, intent = "interview_calls", "critical", "Interview invitation"
    elif any(k in lower for k in ("invoice", "payment due", "amount due")):
        category, priority, intent = "bills", "high", "Invoice / payment due"
    elif any(k in lower for k in ("bank", "statement", "transaction")):
        category, priority, intent = "banking", "high", "Banking alert"
    elif any(k in lower for k in ("order", "shipped", "tracking")):
        category, priority, intent = "orders", "medium", "Order update"
    else:
        category, priority, intent = "personal", "medium", "General"

    return json.dumps(
        {
            "sender_name": None,
            "sender_company": None,
            "category": category,
            "priority": priority,
            "sentiment": "neutral",
            "intent": intent,
            "confidence": 70,
            "summary": f"You received an email about: {subject}.",
            "summary_hi": f"आपको एक नया ईमेल प्राप्त हुआ है: {subject}।",
            "action_items": [],
            "due_dates": [],
            "meeting_requests": [],
            "tracking_numbers": [],
            "invoice_amounts": [],
            "otp_codes": [],
            "payment_requests": [],
            "links": [],
            "labels": [],
            "voice_intro_en": f"New email about {subject}.",
            "voice_intro_hi": f"नया ईमेल: {subject}।",
        }
    )


class AIAnalyzer:
    """Analyze a single email and return structured data."""

    async def analyze(
        self,
        *,
        subject: str,
        sender: str,
        body: str,
        received_at: datetime | None = None,
    ) -> dict[str, Any]:
        prompt = ANALYSIS_USER_PROMPT.format(
            categories=", ".join(CATEGORIES),
            sender=sender,
            subject=subject,
            body=(body or "")[:6000],
        )
        try:
            raw = await _call_llm(
                [SystemMessage(content=ANALYSIS_SYSTEM_PROMPT), HumanMessage(content=prompt)]
            )
            result = _strip_json(raw)
        except Exception as exc:  # noqa: BLE001
            logger.warning("analyzer_failed_fallback", error=str(exc))
            result = _strip_json(_mock_analysis(prompt))

        # Normalize + validate
        result.setdefault("subject", subject)
        result.setdefault("sender", sender)
        result["category"] = self._coerce_category(result.get("category"))
        result["priority"] = self._coerce_priority(result.get("priority"))
        result["confidence"] = float(min(100, max(0, result.get("confidence", 50))))
        for key in (
            "action_items",
            "due_dates",
            "tracking_numbers",
            "otp_codes",
            "links",
            "labels",
        ):
            result.setdefault(key, [])
        for key in (
            "invoice_amounts",
            "payment_requests",
            "meeting_requests",
        ):
            result.setdefault(key, [])
        result.setdefault("summary", "")
        result.setdefault("summary_hi", "")
        return result

    @staticmethod
    def _coerce_category(value: Any) -> str:
        if not value:
            return "other"
        v = str(value).strip().lower().replace(" ", "_").replace("-", "_")
        return v if v in CATEGORIES else "other"

    @staticmethod
    def _coerce_priority(value: Any) -> str:
        v = str(value or "").strip().lower()
        return v if v in {"critical", "high", "medium", "low"} else "medium"


# Singleton convenience
_analyzer: AIAnalyzer | None = None


def get_analyzer() -> AIAnalyzer:
    global _analyzer
    if _analyzer is None:
        _analyzer = AIAnalyzer()
    return _analyzer
