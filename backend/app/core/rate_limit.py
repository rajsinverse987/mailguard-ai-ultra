"""Token-bucket rate limiter backed by Redis."""

from __future__ import annotations

import time
from typing import Any

from redis.asyncio import Redis

from app.config import settings


class TokenBucket:
    def __init__(self, redis: Redis, *, capacity: int, refill_per_sec: float) -> None:
        self.redis = redis
        self.capacity = capacity
        self.refill = refill_per_sec

    async def allow(self, key: str, cost: int = 1) -> bool:
        now = time.time()
        bucket_key = f"rl:{key}"
        data = await self.redis.hgetall(bucket_key)
        tokens = float(data.get(b"tokens", self.capacity))
        last = float(data.get(b"last", now))

        tokens = min(self.capacity, tokens + (now - last) * self.refill)
        if tokens >= cost:
            tokens -= cost
            await self.redis.hset(
                bucket_key,
                mapping={"tokens": tokens, "last": now},
            )
            await self.redis.expire(bucket_key, 60)
            return True
        await self.redis.hset(bucket_key, mapping={"tokens": tokens, "last": now})
        await self.redis.expire(bucket_key, 60)
        return False


_bucket: TokenBucket | None = None


def get_bucket() -> TokenBucket:
    global _bucket
    if _bucket is None:
        from app.db.redis import get_redis

        redis: Redis = get_redis()  # type: ignore[assignment]
        _bucket = TokenBucket(redis, capacity=120, refill_per_sec=2.0)
    return _bucket


async def rate_limit(key: str, cost: int = 1) -> bool:
    return await get_bucket().allow(key, cost)


# Expose for tests
__all__ = ["TokenBucket", "rate_limit", "get_bucket", "settings", "Any"]
