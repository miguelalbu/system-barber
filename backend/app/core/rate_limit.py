"""
In-process sliding-window rate limiter.

Per process on purpose, like the doc's first version (Camada 5): with several
API instances the effective limit multiplies by the instance count. Good enough
for the control plane, whose only caller is the Core; move to Redis when a
limit has to be exact.
"""

from __future__ import annotations

import time
from collections import defaultdict, deque
from threading import Lock

from app.core.exceptions import TooManyRequests


class RateLimiter:
    def __init__(self, limit: int, window_seconds: float = 60.0) -> None:
        self.limit = limit
        self.window = window_seconds
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def hit(self, key: str) -> None:
        now = time.monotonic()
        with self._lock:
            hits = self._hits[key]
            while hits and now - hits[0] > self.window:
                hits.popleft()
            if len(hits) >= self.limit:
                raise TooManyRequests("Muitas requisições — tente de novo em instantes")
            hits.append(now)

    def reset(self) -> None:
        with self._lock:
            self._hits.clear()
