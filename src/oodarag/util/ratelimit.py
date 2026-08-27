"""A token-bucket rate limiter, so connectors are polite to the APIs they hit."""

from __future__ import annotations

import threading
import time


class TokenBucket:
    def __init__(self, rate_per_sec: float, burst: int | None = None) -> None:
        self.rate = max(rate_per_sec, 0.001)
        self.capacity = float(burst if burst is not None else max(1, int(rate_per_sec)))
        self._tokens = self.capacity
        self._last = time.monotonic()
        self._lock = threading.Lock()

    def acquire(self, tokens: float = 1.0) -> float:
        """Block until `tokens` are available. Returns the seconds spent waiting."""
        waited = 0.0
        while True:
            with self._lock:
                now = time.monotonic()
                self._tokens = min(self.capacity, self._tokens + (now - self._last) * self.rate)
                self._last = now
                if self._tokens >= tokens:
                    self._tokens -= tokens
                    return waited
                deficit = tokens - self._tokens
                sleep_for = deficit / self.rate
            time.sleep(min(sleep_for, 5.0))
            waited += min(sleep_for, 5.0)
