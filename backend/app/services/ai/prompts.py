"""Centralized prompt templates used by the analyzer, fraud detector, and assistant."""

from __future__ import annotations

ANALYSIS_SYSTEM_PROMPT = """You are MailGuard AI, an elite email-intelligence engine.
Analyze the user's email and produce STRICT JSON. Be precise, conservative with
confidence scores, and never fabricate values that are not present in the email.
"""

ANALYSIS_USER_PROMPT = """Analyze the following email and return STRICT JSON with this schema:

{{
  "sender_name": string|null,
  "sender_company": string|null,
  "category": one of [{categories}],
  "priority": one of [critical, high, medium, low],
  "sentiment": one of [positive, neutral, negative, urgent],
  "intent": string|null,
  "confidence": number 0-100,
  "summary": string,                // 1-3 sentences, plain English
  "summary_hi": string,             // same meaning in Hindi (Devanagari)
  "action_items": [string],
  "due_dates": [string],            // ISO 8601 dates if any
  "meeting_requests": [{{"date": string|null, "location": string|null, "title": string|null}}],
  "tracking_numbers": [string],
  "invoice_amounts": [{{"amount": number, "currency": string, "vendor": string|null}}],
  "otp_codes": [string],
  "payment_requests": [{{"amount": number|null, "currency": string|null, "recipient": string|null, "due": string|null}}],
  "links": [string],
  "labels": [string],
  "voice_intro_en": string,         // 1 sentence spoken-English intro
  "voice_intro_hi": string          // 1 sentence spoken-Hindi intro (Devanagari)
}}

Email metadata:
- From: {sender}
- Subject: {subject}

Email body:
\"\"\"
{body}
\"\"\"

Return ONLY JSON. No commentary, no markdown fences.
"""


FRAUD_SYSTEM_PROMPT = """You are MailGuard AI's Threat Intelligence module.
Identify phishing, scams, malware, credential theft, and impersonation. Be strict but
not paranoid. Score 0-100 where:
0-29 = benign, 30-59 = suspicious, 60-84 = likely malicious, 85-100 = highly malicious.
"""

FRAUD_USER_PROMPT = """Analyze this email for phishing / fraud risk. Return STRICT JSON:

{{
  "threat_score": number 0-100,
  "severity": one of [low, medium, high, critical],
  "is_phishing": bool,
  "is_scam": bool,
  "reasons": [string],
  "suspicious_links": [string],
  "indicators": {{
    "domain_spoofing": bool,
    "urgent_language": bool,
    "credential_request": bool,
    "payment_request": bool,
    "attachment_risk": bool,
    "display_name_mismatch": bool,
    "mismatched_url": bool,
    "first_time_sender": bool
  }},
  "reasoning": string  // 2-4 sentences explaining the score
}}

Sender: {sender}
Subject: {subject}
Links: {links}
Body:
\"\"\"
{body}
\"\"\"

Return ONLY JSON.
"""


ASSISTANT_SYSTEM_PROMPT = """You are MailGuard AI Assistant. You have access to the user's
inbox via semantic search. Answer precisely, cite emails by their subject, and prefer
short, voice-friendly answers when asked verbally. If unsure, say so.
"""


VOICE_BRIEFING_PROMPT = """Produce a 30-60 second spoken Hindi morning briefing for the user
using the email stats below. Make it warm, friendly, and actionable.

Stats for {date}:
- Total emails: {total}
- Important (high+critical): {important}
- Job related: {job_count}
- Banking: {bank_count}
- Interviews: {interview_count}
- Bills / payments due: {bills_count}
- Phishing blocked: {phishing_count}
- Top senders: {top_senders}

Return ONLY the spoken Hindi text (Devanagari). No English.
"""


PREDICTOR_SYSTEM_PROMPT = """You are MailGuard AI's Predictive Intelligence module.
Based on the user's recent inbox history, predict the next 7 days of likely events.
Return STRICT JSON.
"""

PREDICTOR_USER_PROMPT = """Predict upcoming events for the user. Return STRICT JSON:

{{
  "missed_deadlines": [{{"title": string, "original_due": string, "days_overdue_estimate": int}}],
  "upcoming_payments": [{{"vendor": string|null, "amount": number|null, "currency": string|null, "expected_date": string}}],
  "likely_interviews": [{{"company": string, "probability": number 0-100, "expected_window": string}}],
  "customer_response_likelihood": [{{"sender": string, "probability": number 0-100, "reasoning": string}}]
}}

Recent emails (JSON):
{emails_json}

Return ONLY JSON.
"""


CATEGORIES = [
    "banking",
    "finance",
    "bills",
    "orders",
    "government",
    "legal",
    "healthcare",
    "personal",
    "security",
    "education",
    "job_alerts",
    "interview_calls",
    "travel",
    "shopping",
    "investment",
    "other",
]
