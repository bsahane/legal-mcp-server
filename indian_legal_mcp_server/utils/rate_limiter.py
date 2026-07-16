import time
from collections import defaultdict
from typing import Optional
from indian_legal_mcp_server.config import settings


class RateLimiter:
    def __init__(self):
        self._windows: dict[str, list[float]] = defaultdict(list)

    def check(self, key: str, limit: Optional[int] = None) -> bool:
        limit = limit or settings.RATE_LIMIT_PER_MINUTE
        now = time.time()
        window_start = now - 60
        self._windows[key] = [t for t in self._windows[key] if t > window_start]
        if len(self._windows[key]) >= limit:
            return False
        self._windows[key].append(now)
        return True

    def check_llm(self, key: str) -> bool:
        return self.check(key, settings.RATE_LIMIT_LLM_PER_MINUTE)

    def check_external_api(self, key: str) -> bool:
        return self.check(key, settings.RATE_LIMIT_EXTERNAL_API_PER_MINUTE)


_limiter: Optional[RateLimiter] = None


def get_rate_limiter() -> RateLimiter:
    global _limiter
    if _limiter is None:
        _limiter = RateLimiter()
    return _limiter
