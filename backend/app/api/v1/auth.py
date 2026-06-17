"""Auth endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, SessionDep, get_current_user
from app.core.security import Role, create_access_token, hash_password, verify_password
from app.core.logging import get_logger
from app.models.user import User
from app.schemas.auth import LoginIn, RegisterIn, TokenOut, UserOut, UserUpdate
from app.config import settings

router = APIRouter(prefix="/auth", tags=["auth"])
logger = get_logger(__name__)


@router.post("/register", response_model=UserOut, status_code=201)
async def register(payload: RegisterIn, db: SessionDep) -> UserOut:
    existing = (
        await db.execute(select(User).where(User.email == payload.email.lower()))
    ).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=409, detail="email already registered")

    user = User(
        email=payload.email.lower(),
        full_name=payload.full_name,
        hashed_password=hash_password(payload.password),
        phone=payload.phone,
        preferred_language=payload.preferred_language,
        preferred_voice=payload.preferred_voice,
        role=Role.USER,
        is_active=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return UserOut.model_validate(user)


@router.post("/login", response_model=TokenOut)
async def login(payload: LoginIn, db: SessionDep) -> TokenOut:
    user = (
        await db.execute(select(User).where(User.email == payload.email.lower()))
    ).scalar_one_or_none()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="invalid credentials")
    token = create_access_token(str(user.id), extra={"role": user.role})
    return TokenOut(access_token=token, expires_in=settings.jwt_expire_minutes * 60)


@router.get("/me", response_model=UserOut)
async def me(user: CurrentUser) -> UserOut:
    return UserOut.model_validate(user)


@router.patch("/me", response_model=UserOut)
async def update_me(
    payload: UserUpdate, user: CurrentUser, db: SessionDep
) -> UserOut:
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(user, field, value)
    await db.commit()
    await db.refresh(user)
    return UserOut.model_validate(user)
