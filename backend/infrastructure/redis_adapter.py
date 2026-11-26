import asyncio
from collections.abc import Awaitable
from typing import TypeVar

from redis.asyncio import Redis
from redis.exceptions import RedisError

from backend.application.ports import CacheUnavailableError

T = TypeVar("T")


class RedisCacheAdapter:
    def __init__(self, url: str) -> None:
        self.url = url
        self._client = Redis.from_url(
            url, decode_responses=True,
            socket_connect_timeout=0.2, socket_timeout=0.2,
        )

    async def _execute(self, operation: Awaitable[T]) -> T:
        try:
            return await asyncio.wait_for(operation, timeout=0.4)
        except (RedisError, OSError, TimeoutError) as exc:
            raise CacheUnavailableError("Redis operation failed") from exc

    async def get(self, key: str) -> str | None:
        return await self._execute(self._client.get(key))

    async def set(self, key: str, value: str, ttl_seconds: int = 300) -> None:
        await self._execute(self._client.set(key, value, ex=ttl_seconds))

    async def increment_counter(self, name: str, amount: int = 1) -> int:
        return await self._execute(self._client.incrby(f"counter:{name}", amount))

    async def close(self) -> None:
        await self._client.aclose()