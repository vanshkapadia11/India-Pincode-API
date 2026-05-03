import time
from typing import Any, Optional
from app.logger import logger


class InMemoryCache:
    def __init__(self, ttl_seconds: int = 300):
        self._cache: dict = {}
        self._ttl = ttl_seconds  # default 5 minutes

    def _is_expired(self, entry: dict) -> bool:
        return time.time() > entry["expires_at"]

    def get(self, key: str) -> Optional[Any]:
        if key not in self._cache:
            return None

        entry = self._cache[key]

        if self._is_expired(entry):
            del self._cache[key]
            logger.info(f"🗑️  Cache expired | key:{key}")
            return None

        logger.info(f"⚡ Cache hit | key:{key}")
        return entry["value"]

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        expires_at = time.time() + (ttl or self._ttl)
        self._cache[key] = {"value": value, "expires_at": expires_at}
        logger.info(f"💾 Cache set | key:{key} | ttl:{ttl or self._ttl}s")

    def delete(self, key: str) -> None:
        if key in self._cache:
            del self._cache[key]
            logger.info(f"🗑️  Cache deleted | key:{key}")

    def clear(self) -> None:
        count = len(self._cache)
        self._cache.clear()
        logger.info(f"🗑️  Cache cleared | {count} entries removed")

    def stats(self) -> dict:
        now = time.time()
        total = len(self._cache)
        expired = sum(1 for e in self._cache.values() if now > e["expires_at"])
        return {
            "total_entries": total,
            "active_entries": total - expired,
            "expired_entries": expired,
        }


# single instance used across entire app
cache = InMemoryCache(ttl_seconds=300)  # 5 min default TTL
