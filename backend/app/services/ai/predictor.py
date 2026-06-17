"""Predictive AI: missed deadlines, upcoming payments, interview probability."""

from __future__ import annotations

import json
from typing import Any

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from app.config import settings
from app.core.logging import get_logger
from app.services.ai.prompts import PREDICTOR_SYSTEM_PROMPT, PREDICTOR_USER_PROMPT

logger = get_logger(__name__)


async def predict_next_7_days(emails: list[dict[str, Any]]) -> dict[str, Any]:
    if not emails:
        return {
            "missed_deadlines": [],
            "upcoming_payments": [],
            "likely_interviews": [],
            "customer_response_likelihood": [],
        }
    if not settings.openai_api_key:
        return _heuristic_predictions(emails)

    llm = ChatOpenAI(
        model=settings.openai_model,
        temperature=0.2,
        api_key=settings.openai_api_key,
        model_kwargs={"response_format": {"type": "json_object"}},
    )
    payload = json.dumps(emails[:50], default=str)
    resp = await llm.ainvoke(
        [
            SystemMessage(content=PREDICTOR_SYSTEM_PROMPT),
            HumanMessage(content=PREDICTOR_USER_PROMPT.format(emails_json=payload)),
        ]
    )
    try:
        return json.loads(resp.content)
    except json.JSONDecodeError:
        return _heuristic_predictions(emails)


def _heuristic_predictions(emails: list[dict[str, Any]]) -> dict[str, Any]:
    missed: list[dict[str, Any]] = []
    payments: list[dict[str, Any]] = []
    interviews: list[dict[str, Any]] = []

    for e in emails:
        for due in e.get("due_dates") or []:
            missed.append({"title": e.get("subject"), "original_due": due, "days_overdue_estimate": 0})
        for inv in e.get("invoice_amounts") or []:
            payments.append(
                {
                    "vendor": inv.get("vendor") or e.get("sender_company"),
                    "amount": inv.get("amount"),
                    "currency": inv.get("currency"),
                    "expected_date": (e.get("due_dates") or [""])[0],
                }
            )
        if e.get("category") == "interview_calls":
            interviews.append(
                {
                    "company": e.get("sender_company") or e.get("sender_email"),
                    "probability": 75,
                    "expected_window": "next 7 days",
                }
            )

    return {
        "missed_deadlines": missed[:10],
        "upcoming_payments": payments[:10],
        "likely_interviews": interviews[:10],
        "customer_response_likelihood": [],
    }
