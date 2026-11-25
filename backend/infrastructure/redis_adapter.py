class RedisCacheAdapter:
    """Driven Adapter for Redis Caching Layer and live counters."""

    def __init__(self, url: str) -> None:
        self.url = url

    async def get(self, key: str) -> str | None:
        raise NotImplementedError("Redis GET is not connected yet")

    async def set(self, key: str, value: str, ttl_seconds: int = 300) -> None:
        raise NotImplementedError("Redis SETEX is not connected yet")

    async def increment_counter(self, name: str, amount: int = 1) -> int:
        raise NotImplementedError("Redis INCRBY is not connected yet")