"""Briefings endpoints (manual + history)."""

from __future__ import annotations

import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, SessionDep
from app.models.briefing import Briefing
from app.services.briefings import generate_evening_briefing, generate_morning_briefing
from app.services.messaging.dispatcher import WhatsAppDispatcher
from app.services.voice.tts import get_tts

router = APIRouter(prefix="/briefings", tags=["briefings"])


@router.get("")
async def list_briefings(user: CurrentUser, db: SessionDep, limit: int = 30) -> list[dict]:
    res = await db.execute(
        select(Briefing)
        .where(Briefing.user_id == user.id)
        .order_by(desc(Briefing.created_at))
        .limit(limit)
    )
    return [
        {
            "id": str(b.id),
            "kind": b.kind,
            "period_start": b.period_start,
            "period_end": b.period_end,
            "text": b.text,
            "delivered": b.delivered,
            "stats": b.stats,
            "created_at": b.created_at.isoformat(),
        }
        for b in res.scalars().all()
    ]


@router.post("/morning")
async def trigger_morning(user: CurrentUser, db: SessionDep, day: date | None = None) -> dict:
    briefing = await generate_morning_briefing(db, user, day=day or date.today())
    await db.commit()
    return {"id": str(briefing.id), "text": briefing.text}


@router.post("/evening")
async def trigger_evening(user: CurrentUser, db: SessionDep, day: date | None = None) -> dict:
    briefing = await generate_evening_briefing(db, user, day=day or date.today())
    await db.commit()
    return {"id": str(briefing.id), "text": briefing.text}
