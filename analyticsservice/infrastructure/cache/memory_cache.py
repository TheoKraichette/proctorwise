import time
from typing import Optional, Any

from application.interfaces.cache_store import CacheStore


class InMemoryCacheStore(CacheStore):
    """Cache en memoire pour les analytics."""

    def __init__(self):
        self._cache = {}
        self._expiry = {}

    def get(self, key: str) -> Optional[Any]:
        if key in self._cache:
            if key in self._expiry and time.time() > self._expiry[key]:
                del self._cache[key]
                del self._expiry[key]
                return None
            return self._cache[key]
        return None

    def set(self, key: str, value: Any, ttl_seconds: int = 300) -> None:
        self._cache[key] = value
        self._expiry[key] = time.time() + ttl_seconds

    def delete(self, key: str) -> None:
        self._cache.pop(key, None)
        self._expiry.pop(key, None)

    def exists(self, key: str) -> bool:
        return self.get(key) is not None

    def clear(self) -> None:
        self._cache.clear()
        self._expiry.clear()
