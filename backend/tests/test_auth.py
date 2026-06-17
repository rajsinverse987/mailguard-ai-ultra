"""Tests for auth + JWT."""

from __future__ import annotations

import pytest

from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    has_permission,
    verify_password,
    Role,
)


def test_password_hash_and_verify() -> None:
    # passlib + bcrypt 4.x has a 72-byte input limit; keep it short.
    h = hash_password("s3cret-pwd")
    assert verify_password("s3cret-pwd", h)
    assert not verify_password("wrong", h)


def test_jwt_round_trip() -> None:
    token = create_access_token("user-123", extra={"role": "user"})
    payload = decode_access_token(token)
    assert payload["sub"] == "user-123"
    assert payload["role"] == "user"


def test_permissions() -> None:
    assert has_permission(Role.ADMIN, "anything")
    assert has_permission(Role.USER, "emails:read")
    assert not has_permission(Role.USER, "audit:read")
    assert has_permission(Role.AUDITOR, "audit:read")


def test_invalid_token_raises() -> None:
    import pytest
    from app.core.exceptions import UnauthorizedError

    with pytest.raises(UnauthorizedError):
        decode_access_token("not-a-real-token")
