import time
from typing import Optional, Any
from indian_legal_mcp_server.config import settings

CACHE_CONFIG = {
    "statute_search": {"ttl": 86400},
    "ecourts_lookup": {"ttl": 1800},
    "indiankanoon_search": {"ttl": 3600},
    "limitation_calculator": {"ttl": 0},
    "legal_concepts": {"ttl": 86400},
    "bail_assessment": {"ttl": 0},
}


class CacheManager:
    def __init__(self):
        self._store: dict[str, tuple[float, Any]] = {}

    def get(self, key: str, tool: str = "default") -> Optional[Any]:
        ttl = CACHE_CONFIG.get(tool, {}).get("ttl", 0)
        if ttl == 0:
            return None
        if key in self._store:
            expiry, value = self._store[key]
            if time.time() < expiry:
                return value
            del self._store[key]
        return None

    def set(self, key: str, value: Any, tool: str = "default"):
        ttl = CACHE_CONFIG.get(tool, {}).get("ttl", 0)
        if ttl > 0:
            self._store[key] = (time.time() + ttl, value)

    def clear_tool(self, tool: str):
        pass

    def clear_all(self):
        self._store.clear()


_cache: Optional[CacheManager] = None


def get_cache() -> CacheManager:
    global _cache
    if _cache is None:
        _cache = CacheManager()
    return _cache
