from typing import Optional

import redis


class RedisKV:
    """Thin wrapper for Redis key-value operations (sessions, rate limit)."""

    def __init__(self, url: str):
        self.client = redis.Redis.from_url(url, decode_responses=True)

    def get(self, key: str) -> Optional[str]:
        return self.client.get(key)

    def set(self, key: str, value: str, ex: int | None = None) -> None:
        self.client.set(key, value, ex=ex)


