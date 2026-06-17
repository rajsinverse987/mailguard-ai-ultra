"""Fraud detection endpoints."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, SessionDep
from app.models.fraud_alert import FraudAlert
from app.services.ai.fraud_detector import analyze_threat
from app.services.ai.analyzer import get_analyzer

router = APIRouter(prefix="/fraud", tags=["fraud"])


@router.get("/alerts")
async def list_alerts(
    user: CurrentUser, db: SessionDep, limit: int = Query(100, ge=1, le=500)
) -> list[dict]:
    res = await db.execute(
        select(FraudAlert)
        .where(FraudAlert.user_id == user.id)
        .order_by(desc(FraudAlert.created_at))
        .limit(limit)
    )
    return [
        {
            "id": str(a.id),
            "email_id": str(a.email_id),
            "threat_score": a.threat_score,
            "severity": a.severity,
            "is_phishing": a.is_phishing,
            "is_scam": a.is_scam,
            "reasons": list(a.reasons or []),
            "suspicious_links": list(a.suspicious_links or []),
            "reasoning": a.reasoning,
            "created_at": a.created_at.isoformat(),
            "acknowledged": a.acknowledged,
        }
        for a in res.scalars().all()
    ]


@router.post("/scan")
async def scan_email(payload: dict, user: CurrentUser) -> dict:
    result = await analyze_threat(payload)
    return result


@router.post("/ack/{alert_id}")
async def acknowledge(alert_id: uuid.UUID, user: CurrentUser, db: SessionDep) -> dict:
    alert = await db.get(FraudAlert, alert_id)
    if not alert or alert.user_id != user.id:
        raise HTTPException(status_code=404, detail="not found")
    alert.acknowledged = True
    await db.commit()
    return {"ok": True}
