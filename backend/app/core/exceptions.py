"""Domain-specific exceptions used across the app."""

from __future__ import annotations


class MailGuardError(Exception):
    """Base exception for the application."""

    status_code = 500
    code = "internal_error"

    def __init__(self, message: str = "", *, code: str | None = None) -> None:
        super().__init__(message or self.code)
        self.message = message or self.code
        if code:
            self.code = code


class NotFoundError(MailGuardError):
    status_code = 404
    code = "not_found"


class UnauthorizedError(MailGuardError):
    status_code = 401
    code = "unauthorized"


class ForbiddenError(MailGuardError):
    status_code = 403
    code = "forbidden"


class ValidationError(MailGuardError):
    status_code = 422
    code = "validation_error"


class ConflictError(MailGuardError):
    status_code = 409
    code = "conflict"


class RateLimitError(MailGuardError):
    status_code = 429
    code = "rate_limited"


class UpstreamError(MailGuardError):
    status_code = 502
    code = "upstream_error"


class FraudDetected(MailGuardError):
    status_code = 200  # signals an alert rather than an error
    code = "fraud_detected"
