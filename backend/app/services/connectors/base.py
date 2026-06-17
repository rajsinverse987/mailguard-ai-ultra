"""Base connector — defines the contract for all email providers."""

from __future__ import annotations

import abc
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class RawEmail:
    """Provider-agnostic email representation."""

    provider: str
    message_id: str
    thread_id: str | None
    subject: str
    sender_email: str
    sender_name: str | None
    to: list[str] = field(default_factory=list)
    cc: list[str] = field(default_factory=list)
    body_text: str = ""
    body_html: str | None = None
    snippet: str | None = None
    received_at: datetime | None = None
    labels: list[str] = field(default_factory=list)
    links: list[str] = field(default_factory=list)
    attachments: list[dict[str, Any]] = field(default_factory=list)
    raw: dict[str, Any] = field(default_factory=dict)


class BaseConnector(abc.ABC):
    """Abstract base for email providers."""

    provider: str = "base"

    @abc.abstractmethod
    async def fetch_new(self, *, since: datetime | None = None) -> list[RawEmail]: ...

    @abc.abstractmethod
    async def fetch_message(self, message_id: str) -> RawEmail: ...

    @abc.abstractmethod
    async def setup_watch(self) -> dict[str, Any]: ...
