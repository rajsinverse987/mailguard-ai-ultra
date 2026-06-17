"""Async Redis singleton for cache + broker."""

from __future__ import annotations

from functools import lru_cache

from redis.asyncio import Redis

from app.config import settings


@lru_cache(maxsize=1)
def get_redis() -> Redis:
    return Redis.from_url(
        str(settings.redis_url),
        encoding="utf-8",
        decode_responses=False,
        max_connections=64,
    )


async def close_redis() -> None:
    await get_redis().aclose()
