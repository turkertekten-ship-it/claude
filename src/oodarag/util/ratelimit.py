"""A token-bucket rate limiter, so connectors are polite to the APIs they hit.

The failure mode this exists to prevent is the one that ends a run permanently:
a connector walks a paginated listing as fast as urllib will go, trips the
provider's abuse detector, and the credential comes back 403 for everything
afterwards. A bucket rather than a flat sleep because that is the shape real
APIs actually price - a burst is forgiven, a sustained rate is not - so the
first `burst` requests go out immediately and the rest settle to `rate_per_sec`.

Three properties are load-bearing rather than incidental.

The clock is `time.monotonic`. A wall clock stepped backwards by NTP mid-run
would hand out free tokens; stepped forwards, it would refill the bucket from
time that never elapsed. Elapsed time is clamped at zero anyway, because an
injected clock is only as monotonic as its caller.

`acquire` sleeps for the computed deficit instead of polling. A busy-wait would
burn a core per blocked connector, which is a strange way to spend the time a
rate limiter exists to waste.

No request can wait forever. The bucket cannot hold more than `capacity`, so
asking for more than that is a condition that will never come true; it is
clamped instead of hung on. Likewise a capacity or rate of zero, which arrive
from config, not from code, and must degrade to "slow" rather than "stuck".

The clock and the sleep are injectable so tests can drive a bucket across
minutes without spending them.
"""

from __future__ import annotations

import threading
import time
from collections.abc import Callable

#: Longest single sleep. Waking periodically keeps a badly configured (very
#: slow) bucket responsive to Ctrl-C rather than parking uninterruptibly for the
#: whole deficit.
MAX_SLEEP_S = 5.0

#: Slack on the "is a token available yet" comparison. A refill computed in
#: floating point lands a hair under the amount it should have hit exactly (0.2s
#: at 5 tokens/s is 0.9999999999999 tokens, not 1.0). Without the slack the
#: waiter wakes, finds itself a picosecond short, and sleeps again for
#: picoseconds - a spin wearing a sleep's clothes.
EPSILON = 1e-9

#: Floor on the rate. Zero is a divide-by-zero when sizing the wait and a
#: negative rate is always a config error; both become "one token per ~17
#: minutes", which stalls loudly instead of crashing an otherwise healthy run.
MIN_RATE = 0.001


class TokenBucket:
    """A thread-safe token bucket. `acquire` blocks by sleeping; it never spins."""

    def __init__(
        self,
        rate_per_sec: float,
        burst: int | None = None,
        *,
        monotonic: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self.rate = max(float(rate_per_sec), MIN_RATE)
        # A capacity of zero is a deadlock, not a rate limit: nothing would ever
        # become acquirable. burst<=0 therefore reads as "no burst allowance" -
        # a single token, refilled at `rate`.
        raw_burst = burst if burst is not None else int(rate_per_sec)
        self.capacity = max(1.0, float(raw_burst))
        self._tokens = self.capacity
        self._monotonic = monotonic
        self._sleep = sleep
        self._last = self._monotonic()
        self._lock = threading.Lock()

    def _refill_locked(self) -> float:
        """Credit elapsed time to the bucket. Returns the clock reading used."""
        now = self._monotonic()
        # Clamped at zero: a clock that went backwards must not drain the bucket,
        # and it must not make `waited` negative either.
        elapsed = max(0.0, now - self._last)
        self._last = now
        self._tokens = min(self.capacity, self._tokens + elapsed * self.rate)
        return now

    def acquire(self, tokens: float = 1.0) -> float:
        """Block until `tokens` are available. Returns the seconds spent waiting.

        A request for more than `capacity` is clamped: the bucket can never hold
        that many, so honouring it literally would block until the process is
        killed. A negative request is clamped to zero rather than used to mint
        tokens the caller never earned.
        """
        want = min(max(float(tokens), 0.0), self.capacity)
        started = self._monotonic()
        while True:
            with self._lock:
                now = self._refill_locked()
                if self._tokens >= want - EPSILON:
                    # Clamped: the epsilon above can leave a negative sliver,
                    # and a bucket that drifts below empty never refills level.
                    self._tokens = max(0.0, self._tokens - want)
                    return max(0.0, now - started)
                deficit = want - self._tokens
            # Slept outside the lock: holding it here would serialise every other
            # thread behind this one's wait instead of behind the bucket.
            self._sleep(min(deficit / self.rate, MAX_SLEEP_S))
