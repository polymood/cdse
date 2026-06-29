"""A small thread safe token bucket rate limiter.

This provides proactive client side throttling so that bursts of requests stay
under a configured per minute ceiling. It is deliberately simple and blocking;
the sleeping is isolated here so that an asynchronous variant can later replace
the wait without touching the calling code.
"""

from __future__ import annotations

import threading
import time


class RateLimiter:
    """Limit the rate of an operation using the token bucket algorithm.

    When ``rate_per_minute`` is ``None`` the limiter is disabled and
    :meth:`acquire` returns immediately.
    """

    def __init__(self, rate_per_minute: int | None) -> None:
        if rate_per_minute is not None and rate_per_minute > 0:
            self._enabled = True
            self._capacity = float(rate_per_minute)
            self._refill_per_second = self._capacity / 60.0
        else:
            self._enabled = False
            self._capacity = 0.0
            self._refill_per_second = 0.0
        self._tokens = self._capacity
        self._updated = time.monotonic()
        self._lock = threading.Lock()

    def acquire(self) -> None:
        """Block until a single token is available, then consume it."""
        if not self._enabled:
            return
        while True:
            with self._lock:
                now = time.monotonic()
                elapsed = now - self._updated
                self._updated = now
                self._tokens = min(
                    self._capacity, self._tokens + elapsed * self._refill_per_second
                )
                if self._tokens >= 1.0:
                    self._tokens -= 1.0
                    return
                wait = (1.0 - self._tokens) / self._refill_per_second
            time.sleep(wait)
