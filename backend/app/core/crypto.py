"""AES-GCM field-level encryption for sensitive tokens (OAuth refresh tokens etc.)."""

from __future__ import annotations

import base64
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.config import settings


class FieldCipher:
    """AES-GCM helper. Encrypts strings with a per-record nonce.

    The wire format is `nonce:ciphertext`, both base64-encoded."""

    def __init__(self, key_b64: str | None = None) -> None:
        key = base64.b64decode(key_b64 or settings.aes_secret)
        if len(key) not in (16, 24, 32):
            raise ValueError("AES key must be 16, 24, or 32 bytes")
        self._aes = AESGCM(key)

    def encrypt(self, plaintext: str, *, aad: bytes | None = None) -> str:
        nonce = os.urandom(12)
        ct = self._aes.encrypt(nonce, plaintext.encode("utf-8"), aad)
        return base64.b64encode(nonce).decode() + ":" + base64.b64encode(ct).decode()

    def decrypt(self, token: str, *, aad: bytes | None = None) -> str:
        try:
            nonce_b64, ct_b64 = token.split(":", 1)
            nonce = base64.b64decode(nonce_b64)
            ct = base64.b64decode(ct_b64)
        except ValueError as exc:
            raise ValueError("malformed ciphertext") from exc
        return self._aes.decrypt(nonce, ct, aad).decode("utf-8")


cipher = FieldCipher()
