"""JWT issuance / verification, password hashing, RBAC primitives."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings
from app.core.exceptions import UnauthorizedError

_pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")


# --- Password helpers ------------------------------------------------------
def hash_password(plain: str) -> str:
    return _pwd.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return _pwd.verify(plain, hashed)


# --- JWT helpers -----------------------------------------------------------
def create_access_token(
    subject: str,
    *,
    expires_minutes: int | None = None,
    extra: dict[str, Any] | None = None,
) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=expires_minutes or settings.jwt_expire_minutes
    )
    payload: dict[str, Any] = {
        "sub": subject,
        "exp": int(expire.timestamp()),
        "iat": int(datetime.now(timezone.utc).timestamp()),
        "iss": settings.app_name,
    }
    if extra:
        payload.update(extra)
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict[str, Any]:
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except JWTError as exc:
        raise UnauthorizedError("Invalid or expired token") from exc


# --- RBAC -------------------------------------------------------------------
class Role:
    ADMIN = "admin"
    USER = "user"
    AUDITOR = "auditor"


PERMISSIONS: dict[str, set[str]] = {
    Role.ADMIN: {"*"},
    Role.USER: {
        "emails:read",
        "emails:write",
        "notifications:read",
        "assistant:use",
        "search:use",
    },
    Role.AUDITOR: {"emails:read", "notifications:read", "audit:read"},
}


def has_permission(role: str, perm: str) -> bool:
    granted = PERMISSIONS.get(role, set())
    return "*" in granted or perm in granted
