"""Tests for the three utilities the rest of the stack leans on.

Each module here has one property that everything above it assumes and nothing
above it checks:

`hashing` must produce the same digest in a different process on a different
machine, because incremental ingest decides "unchanged" by comparing a hash it
computed last night with one it computes tonight. So the digests are pinned as
literals, and the cross-process claim is tested by actually spawning processes
with different hash seeds rather than by trusting the docstring.

`ratelimit` gates every outbound request, so the interesting cases are the ones
where it must *not* block forever: a rate of zero, a burst of zero, a request
larger than the bucket, a clock that has stopped. The clock and the sleep are
injected; no test here spends a real second.

`logging` writes to stderr only - a line on stdout would corrupt `ooda ... --json`
- and must emit exactly one parseable JSON object per event even when a field
value is hostile (a newline, a quote, a reference cycle, an object whose
`__repr__` raises). The tests capture the stream and parse it back.
"""

from __future__ import annotations

import collections
import contextlib
import io
import json
import os
import subprocess
import sys
import threading
import unittest
from collections.abc import Iterator
from pathlib import Path
from unittest import mock

from oodarag.util import hashing
from oodarag.util.hashing import blake_bucket, blake_sign, content_hash, sha256_hex, stable_id
from oodarag.util.logging import Logger, get_logger
from oodarag.util.ratelimit import MAX_SLEEP_S, MIN_RATE, TokenBucket

# ---------------------------------------------------------------- fake clock


class Blocked(Exception):
    """Raised instead of sleeping past the test's patience.

    A bucket that would block forever must fail a test in milliseconds, not
    hang the suite until someone kills it.
    """

    def __init__(self, requested: float) -> None:
        super().__init__(f"would have slept {requested}s")
        self.requested = requested


class FakeClock:
    """A monotonic clock the test drives by hand.

    `sleep` advances it, which is what a real sleep does; a clock that does not
    advance on sleep (`advance_on_sleep=False`) stands in for a suspended host.
    """

    def __init__(
        self,
        start: float = 1000.0,
        *,
        advance_on_sleep: bool = True,
        max_sleeps: int = 10_000,
    ) -> None:
        self.now = start
        self.sleeps: list[float] = []
        self.advance_on_sleep = advance_on_sleep
        self.max_sleeps = max_sleeps

    def monotonic(self) -> float:
        return self.now

    def sleep(self, seconds: float) -> None:
        self.sleeps.append(seconds)
        if len(self.sleeps) > self.max_sleeps:
            raise Blocked(seconds)
        if self.advance_on_sleep:
            self.now += seconds

    def advance(self, seconds: float) -> None:
        self.now += seconds


def bucket(rate: float, burst: int | None = None, clock: FakeClock | None = None) -> tuple:
    clock = clock or FakeClock()
    return TokenBucket(rate, burst, monotonic=clock.monotonic, sleep=clock.sleep), clock


# ------------------------------------------------------------------- capture


class RecordingStream(io.StringIO):
    """A stderr stand-in that counts `write` calls.

    One event has to be one write: `print` issues two (body, then newline) and
    two threads logging at once can interleave between them.
    """

    def __init__(self) -> None:
        super().__init__()
        self.writes: list[str] = []

    def write(self, s: str) -> int:
        self.writes.append(s)
        return super().write(s)


@contextlib.contextmanager
def captured() -> Iterator[tuple[io.StringIO, io.StringIO]]:
    """Capture stderr and stdout separately, so "stdout stayed clean" is testable."""
    err, out = io.StringIO(), io.StringIO()
    with contextlib.redirect_stderr(err), contextlib.redirect_stdout(out):
        yield err, out


def lines(stream: io.StringIO) -> list[str]:
    return stream.getvalue().splitlines()


def records(stream: io.StringIO) -> list[dict]:
    return [json.loads(line) for line in lines(stream)]


# ------------------------------------------------------------------- hashing


class HashDeterminismTestCase(unittest.TestCase):
    """The digests are a wire format: pinned literals, not recomputed expectations."""

    def test_known_digests_are_frozen(self) -> None:
        self.assertEqual(
            sha256_hex("a"),
            "aaa8be88bd4afa32f5b8af336bd2218492836d5edac8fca0e6c3ebc99614678e",
        )
        self.assertEqual(
            sha256_hex("a", "b"),
            "726840df45a968754d1e8b973e45b2f9bc69f9bdf86eef72654e334873335a09",
        )
        self.assertEqual(content_hash("hello world", "Title"), "baa4b8e45fabdb19")
        self.assertEqual(stable_id("github", "owner/repo#1"), "d138711de1d693852d4befc9")

    def test_no_parts_hashes_the_empty_input(self) -> None:
        self.assertEqual(
            sha256_hex(),
            "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        )

    def test_repeated_calls_agree(self) -> None:
        self.assertEqual(sha256_hex("x", "y"), sha256_hex("x", "y"))
        self.assertEqual(content_hash("x"), content_hash("x"))

    def test_digest_is_stable_across_processes_and_hash_seeds(self) -> None:
        # The module docstring's whole claim: builtin hash() is salted per
        # process, so these helpers must not be built on anything that is.
        src = str(Path(hashing.__file__).resolve().parents[2])
        probe = (
            "from oodarag.util.hashing import blake_bucket, content_hash, sha256_hex\n"
            "print(sha256_hex('a', 'b'), content_hash('x'), blake_bucket('tok', 1024))"
        )
        outputs = []
        for seed in ("0", "1", "random"):
            env = dict(os.environ, PYTHONPATH=src, PYTHONHASHSEED=seed)
            proc = subprocess.run(
                [sys.executable, "-c", probe],
                capture_output=True, text=True, env=env, timeout=60, check=True,
            )
            outputs.append(proc.stdout.strip())

        expected = f"{sha256_hex('a', 'b')} {content_hash('x')} {blake_bucket('tok', 1024)}"
        self.assertEqual(outputs, [expected, expected, expected])


class HashFramingTestCase(unittest.TestCase):
    """Part boundaries must survive concatenation, whatever the parts contain."""

    def test_boundary_between_parts_is_not_ambiguous(self) -> None:
        self.assertNotEqual(sha256_hex("ab", "c"), sha256_hex("a", "bc"))
        self.assertNotEqual(sha256_hex("ab", "c"), sha256_hex("abc"))

    def test_a_part_containing_the_separator_is_still_unambiguous(self) -> None:
        # Regression: a bare trailing separator only moves the collision to
        # inputs that contain the separator, and document text contains anything.
        self.assertNotEqual(sha256_hex("a\x1f", "b"), sha256_hex("a", "\x1fb"))
        self.assertNotEqual(sha256_hex("a\x1fb"), sha256_hex("a", "b"))
        self.assertNotEqual(sha256_hex("2\x1fab"), sha256_hex("ab"))

    def test_empty_parts_are_significant(self) -> None:
        digests = {
            sha256_hex(),
            sha256_hex(""),
            sha256_hex("", ""),
            sha256_hex("a"),
            sha256_hex("a", ""),
            sha256_hex("", "a"),
        }
        self.assertEqual(len(digests), 6)

    def test_argument_order_matters(self) -> None:
        self.assertNotEqual(sha256_hex("a", "b"), sha256_hex("b", "a"))


class HashEncodingTestCase(unittest.TestCase):
    def test_unicode_is_hashed_as_utf8_bytes(self) -> None:
        self.assertEqual(content_hash("café"), "d0a542e413f0d29a")
        self.assertEqual(sha256_hex("café"), sha256_hex("caf\u00e9"))
        # NFC and NFD are different strings; hashing does not normalize for you.
        self.assertNotEqual(sha256_hex("caf\u00e9"), sha256_hex("cafe\u0301"))

    def test_lone_surrogates_hash_distinctly_instead_of_collapsing(self) -> None:
        # Paths decoded with surrogateescape carry these. Under errors="replace"
        # every one of them becomes "?" and distinct ids become one id.
        distinct = {sha256_hex("a\udcffb"), sha256_hex("a\udcfeb"), sha256_hex("a?b")}
        self.assertEqual(len(distinct), 3)

    def test_astral_and_control_characters_do_not_raise(self) -> None:
        for text in ("\U0001f600 emoji", "\x00\x01null", "\r\n", "\x1f" * 8):
            self.assertEqual(len(sha256_hex(text)), 64)


class HashShapeTestCase(unittest.TestCase):
    def test_short_forms_are_prefixes_of_the_full_digest(self) -> None:
        full = sha256_hex("doc", "42")
        self.assertEqual(content_hash("doc", "42"), full[:16])
        self.assertEqual(stable_id("doc", "42"), full[:24])

    def test_short_forms_are_lowercase_hex_of_the_documented_width(self) -> None:
        digest = stable_id("a")
        self.assertEqual(len(digest), 24)
        self.assertEqual(len(content_hash("a")), 16)
        self.assertTrue(all(c in "0123456789abcdef" for c in digest))

    def test_distinct_inputs_stay_distinct_at_the_truncated_width(self) -> None:
        ids = {stable_id("src", f"doc-{i}") for i in range(2000)}
        self.assertEqual(len(ids), 2000)


class BlakeBucketTestCase(unittest.TestCase):
    def test_result_is_inside_the_range(self) -> None:
        for i in range(500):
            self.assertIn(blake_bucket(f"token-{i}", 7), range(7))

    def test_is_deterministic(self) -> None:
        self.assertEqual(blake_bucket("chunking", 4096), blake_bucket("chunking", 4096))
        self.assertEqual(blake_bucket("chunking", 4096, salt="s"), blake_bucket("chunking", 4096, "s"))

    def test_salt_moves_tokens_to_other_buckets(self) -> None:
        tokens = [f"token-{i}" for i in range(200)]
        plain = [blake_bucket(t, 64) for t in tokens]
        salted = [blake_bucket(t, 64, salt="pepper") for t in tokens]
        self.assertNotEqual(plain, salted)

    def test_distribution_covers_the_whole_range(self) -> None:
        counts = collections.Counter(blake_bucket(f"tok{i}", 8) for i in range(4000))
        self.assertEqual(sorted(counts), list(range(8)))
        # Loose bound: this is a hash, not an RNG, but a broken mask or a
        # truncated digest would pile everything into a corner of the range.
        for value in counts.values():
            self.assertGreater(value, 350)
            self.assertLess(value, 650)

    def test_full_width_range_is_reachable(self) -> None:
        buckets = 1 << 20
        seen = {blake_bucket(f"t{i}", buckets) for i in range(5000)}
        self.assertGreater(len(seen), 4900)  # no clustering into a small subrange
        self.assertGreater(max(seen), buckets // 2)  # the high half is used at all

    def test_one_bucket_maps_everything_to_zero(self) -> None:
        self.assertEqual({blake_bucket(f"t{i}", 1) for i in range(50)}, {0})

    def test_zero_or_negative_buckets_degrade_instead_of_raising(self) -> None:
        # A dimension of zero is a config error; it must not surface as a
        # ZeroDivisionError from inside a feature hasher, nor as a negative index.
        self.assertEqual(blake_bucket("t", 0), 0)
        self.assertEqual(blake_bucket("t", -5), 0)

    def test_empty_token_is_hashable(self) -> None:
        self.assertIn(blake_bucket("", 16), range(16))


class BlakeSignTestCase(unittest.TestCase):
    def test_only_ever_plus_or_minus_one(self) -> None:
        self.assertEqual({blake_sign(f"t{i}") for i in range(500)}, {1, -1})

    def test_is_deterministic(self) -> None:
        self.assertEqual(blake_sign("retrieval"), blake_sign("retrieval"))

    def test_signs_are_roughly_balanced(self) -> None:
        total = sum(blake_sign(f"t{i}") for i in range(2000))
        self.assertLess(abs(total), 200)  # collisions cancel only if the sign is fair

    def test_salt_changes_the_assignment(self) -> None:
        tokens = [f"t{i}" for i in range(200)]
        self.assertNotEqual(
            [blake_sign(t) for t in tokens],
            [blake_sign(t, salt="other") for t in tokens],
        )

    def test_surrogates_do_not_raise(self) -> None:
        self.assertIn(blake_sign("a\udcffb"), (1, -1))


# ----------------------------------------------------------------- ratelimit


class TokenBucketBurstTestCase(unittest.TestCase):
    def test_burst_is_spent_before_anything_waits(self) -> None:
        bkt, clock = bucket(2.0, 3)

        self.assertEqual([bkt.acquire() for _ in range(3)], [0.0, 0.0, 0.0])
        self.assertEqual(clock.sleeps, [])

    def test_the_request_after_the_burst_waits_one_refill(self) -> None:
        bkt, clock = bucket(2.0, 3)
        for _ in range(3):
            bkt.acquire()

        waited = bkt.acquire()

        self.assertAlmostEqual(waited, 0.5)  # 1 token at 2/s
        self.assertEqual(clock.sleeps, [0.5])

    def test_refill_is_proportional_to_elapsed_time(self) -> None:
        bkt, clock = bucket(2.0, 10)
        for _ in range(10):
            bkt.acquire()

        clock.advance(1.5)  # 3 tokens at 2/s

        self.assertEqual([bkt.acquire() for _ in range(3)], [0.0, 0.0, 0.0])
        self.assertEqual(clock.sleeps, [])
        self.assertAlmostEqual(bkt.acquire(), 0.5)

    def test_idle_time_cannot_bank_more_than_burst(self) -> None:
        bkt, clock = bucket(5.0, 4)
        clock.advance(3600.0)  # an hour of doing nothing: 18000 tokens' worth

        free = [bkt.acquire() for _ in range(4)]

        self.assertEqual(free, [0.0] * 4)
        self.assertAlmostEqual(bkt.acquire(), 0.2)  # the fifth still pays

    def test_default_burst_follows_the_rate(self) -> None:
        bkt, clock = bucket(4.0)
        self.assertEqual([bkt.acquire() for _ in range(4)], [0.0] * 4)
        self.assertAlmostEqual(bkt.acquire(), 0.25)

    def test_fractional_rate_still_allows_one_token(self) -> None:
        bkt, _clock = bucket(0.5)  # int(0.5) == 0 would be a zero-capacity bucket
        self.assertEqual(bkt.capacity, 1.0)
        self.assertEqual(bkt.acquire(), 0.0)


class TokenBucketDegenerateTestCase(unittest.TestCase):
    """The inputs that arrive from config, not from code."""

    def test_zero_burst_is_a_slow_bucket_not_a_deadlock(self) -> None:
        bkt, clock = bucket(2.0, 0)

        self.assertEqual(bkt.capacity, 1.0)
        self.assertEqual(bkt.acquire(), 0.0)
        self.assertAlmostEqual(bkt.acquire(), 0.5)
        self.assertEqual(clock.sleeps, [0.5])

    def test_negative_burst_is_treated_as_no_burst(self) -> None:
        bkt, _clock = bucket(1.0, -10)
        self.assertEqual(bkt.capacity, 1.0)
        self.assertEqual(bkt.acquire(), 0.0)

    def test_zero_rate_neither_divides_by_zero_nor_spins(self) -> None:
        bkt, clock = bucket(0.0, 1)

        self.assertEqual(bkt.rate, MIN_RATE)
        self.assertEqual(bkt.acquire(), 0.0)  # the initial token is still there
        waited = bkt.acquire()

        self.assertAlmostEqual(waited, 1.0 / MIN_RATE, places=3)
        # Sleeping, not polling: every nap is a real one and none exceeds the cap.
        self.assertTrue(all(0.0 < nap <= MAX_SLEEP_S for nap in clock.sleeps))
        self.assertEqual(len(clock.sleeps), 200)

    def test_negative_rate_degrades_to_the_floor(self) -> None:
        bkt, _clock = bucket(-3.0, 2)
        self.assertEqual(bkt.rate, MIN_RATE)

    def test_request_bigger_than_the_bucket_is_clamped_not_hung(self) -> None:
        bkt, clock = bucket(5.0, 2)
        bkt.acquire(2.0)  # drain

        waited = bkt.acquire(50.0)  # can never fit: capacity is 2

        self.assertAlmostEqual(waited, 0.4)  # waits for a full bucket, then proceeds
        self.assertEqual(clock.sleeps, [0.4])

    def test_zero_and_negative_requests_do_not_mint_tokens(self) -> None:
        bkt, clock = bucket(1.0, 2)
        bkt.acquire(2.0)  # drain

        self.assertEqual(bkt.acquire(0.0), 0.0)
        self.assertEqual(bkt.acquire(-5.0), 0.0)
        self.assertEqual(clock.sleeps, [])
        # The negative request must not have refunded the bucket.
        self.assertAlmostEqual(bkt.acquire(1.0), 1.0)


class TokenBucketClockTestCase(unittest.TestCase):
    def test_clock_running_backwards_does_not_drain_the_bucket(self) -> None:
        clock = FakeClock()
        bkt, _ = bucket(1.0, 1, clock)
        bkt.acquire()
        clock.now -= 100.0  # an injected wall clock stepped back by NTP

        waited = bkt.acquire()

        self.assertAlmostEqual(waited, 1.0)  # one token at 1/s, not 101 seconds
        self.assertEqual(clock.sleeps, [1.0])

    def test_a_stopped_clock_never_hands_out_unearned_tokens(self) -> None:
        clock = FakeClock(advance_on_sleep=False, max_sleeps=3)
        bkt, _ = bucket(10.0, 2, clock)
        bkt.acquire()
        bkt.acquire()

        with self.assertRaises(Blocked) as caught:
            bkt.acquire()

        self.assertAlmostEqual(caught.exception.requested, 0.1)
        self.assertEqual(clock.sleeps, [0.1, 0.1, 0.1, 0.1])

    def test_wait_is_measured_on_the_clock_not_estimated(self) -> None:
        clock = FakeClock()
        bkt, _ = bucket(1.0, 1, clock)
        bkt.acquire()

        waited = bkt.acquire()

        self.assertAlmostEqual(waited, sum(clock.sleeps))

    def test_a_wait_ends_in_one_nap_even_when_the_refill_is_not_representable(self) -> None:
        # Regression: 1/3 of a second at 3 tokens/s refills 0.999999999999909
        # tokens, not 1.0. Comparing exactly sends the waiter back to sleep for
        # picoseconds, over and over - a spin that looks like a wait in a trace.
        clock = FakeClock()
        bkt, _ = bucket(3.0, 1, clock)
        bkt.acquire()

        waited = bkt.acquire()

        self.assertEqual(len(clock.sleeps), 1)
        self.assertAlmostEqual(waited, 1 / 3)
        self.assertTrue(all(nap > 0.0 for nap in clock.sleeps))

    def test_a_long_wait_is_broken_into_capped_naps(self) -> None:
        clock = FakeClock()
        bkt, _ = bucket(0.1, 1, clock)  # one token per 10s
        bkt.acquire()

        waited = bkt.acquire()

        self.assertAlmostEqual(waited, 10.0)
        self.assertEqual(clock.sleeps, [MAX_SLEEP_S, MAX_SLEEP_S])

    def test_real_clock_is_the_default(self) -> None:
        # No injection: the default must be monotonic and must not sleep for a
        # request the fresh bucket can already serve.
        bkt = TokenBucket(1000.0, 5)
        self.assertLess(bkt.acquire(), 0.05)


class TokenBucketThreadTestCase(unittest.TestCase):
    def test_threads_cannot_overdraw_the_bucket(self) -> None:
        # The clock never advances and any wait raises, so exactly `capacity`
        # acquires can succeed. A missing lock shows up as a 51st winner.
        clock = FakeClock(advance_on_sleep=False, max_sleeps=0)
        bkt, _ = bucket(1.0, 50, clock)
        wins: list[float] = []
        losses: list[str] = []

        def worker() -> None:
            for _ in range(6):
                try:
                    wins.append(bkt.acquire())
                except Blocked:
                    losses.append("blocked")

        threads = [threading.Thread(target=worker) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=10)

        self.assertFalse([t for t in threads if t.is_alive()])
        self.assertEqual(len(wins), 50)
        self.assertEqual(len(losses), 10)


# ------------------------------------------------------------------- logging


class LoggerLevelTestCase(unittest.TestCase):
    def test_default_level_keeps_info_and_drops_debug(self) -> None:
        log = Logger("t")
        with captured() as (err, _out):
            log.debug("dropped")
            log.info("kept")

        self.assertEqual(len(lines(err)), 1)
        self.assertIn("kept", err.getvalue())

    def test_threshold_is_inclusive_at_its_own_level(self) -> None:
        log = Logger("t", level="warn")
        with captured() as (err, _out):
            log.debug("no")
            log.info("no")
            log.warn("yes")
            log.error("yes")

        self.assertEqual(len(lines(err)), 2)
        self.assertNotIn("no", err.getvalue())

    def test_debug_level_keeps_everything(self) -> None:
        log = Logger("t", level="debug")
        with captured() as (err, _out):
            for method in (log.debug, log.info, log.warn, log.error):
                method("x")

        self.assertEqual(len(lines(err)), 4)

    def test_silent_suppresses_even_errors(self) -> None:
        log = Logger("t", level="silent")
        with captured() as (err, _out):
            log.error("this is on fire")

        self.assertEqual(err.getvalue(), "")

    def test_unknown_level_name_falls_back_to_info(self) -> None:
        log = Logger("t", level="loud")

        self.assertEqual(log.level, 20)
        with captured() as (err, _out):
            log.debug("dropped")
            log.info("kept")
        self.assertEqual(len(lines(err)), 1)

    def test_level_name_is_case_and_whitespace_insensitive(self) -> None:
        self.assertEqual(Logger("t", level=" DEBUG ").level, 10)
        self.assertEqual(Logger("t", level="Warn").level, 30)


    def test_a_filtered_event_never_touches_its_fields(self) -> None:
        # The level check comes first, so a debug call carrying something
        # expensive or hostile costs nothing when debug is off.
        class Hostile:
            def __repr__(self) -> str:
                raise AssertionError("formatted a filtered event")

            def __str__(self) -> str:
                raise AssertionError("formatted a filtered event")

        log = Logger("t", level="info", json_mode=True)
        with captured() as (err, _out):
            log.debug("dropped", obj=Hostile())

        self.assertEqual(err.getvalue(), "")


class LoggerEnvironmentTestCase(unittest.TestCase):
    def test_level_comes_from_the_environment(self) -> None:
        with mock.patch.dict(os.environ, {"OODARAG_LOG_LEVEL": "error"}):
            log = Logger("t")
        self.assertEqual(log.level, 40)

    def test_unknown_environment_level_still_logs(self) -> None:
        with mock.patch.dict(os.environ, {"OODARAG_LOG_LEVEL": "verbose"}):
            log = Logger("t")
        self.assertEqual(log.level, 20)

    def test_empty_environment_level_is_the_default(self) -> None:
        with mock.patch.dict(os.environ, {"OODARAG_LOG_LEVEL": "  "}):
            log = Logger("t")
        self.assertEqual(log.level, 20)

    def test_json_format_comes_from_the_environment(self) -> None:
        with mock.patch.dict(os.environ, {"OODARAG_LOG_FORMAT": "JSON"}):
            log = Logger("t")
        self.assertTrue(log.json_mode)

        with mock.patch.dict(os.environ, {"OODARAG_LOG_FORMAT": "pretty"}):
            self.assertFalse(Logger("t").json_mode)

    def test_arguments_beat_the_environment(self) -> None:
        env = {"OODARAG_LOG_LEVEL": "silent", "OODARAG_LOG_FORMAT": "json"}
        with mock.patch.dict(os.environ, env):
            log = Logger("t", level="debug", json_mode=False)

        self.assertEqual(log.level, 10)
        self.assertFalse(log.json_mode)

    def test_json_mode_false_is_honoured_over_a_json_environment(self) -> None:
        # `json_mode=False` is a decision, not an absent argument.
        with mock.patch.dict(os.environ, {"OODARAG_LOG_FORMAT": "json"}):
            self.assertFalse(Logger("t", json_mode=False).json_mode)

    def test_get_logger_reads_the_environment_and_names_the_logger(self) -> None:
        with mock.patch.dict(os.environ, {"OODARAG_LOG_LEVEL": "debug"}):
            log = get_logger("ingest.web")

        self.assertIsInstance(log, Logger)
        self.assertEqual(log.name, "ingest.web")
        self.assertEqual(log.level, 10)


class LoggerStreamTestCase(unittest.TestCase):
    def test_text_mode_never_touches_stdout(self) -> None:
        log = Logger("http", level="debug", json_mode=False)
        with captured() as (err, out):
            log.info("fetched", url="https://example.test/a")

        self.assertEqual(out.getvalue(), "")
        self.assertEqual(lines(err), ["  [http] fetched url=https://example.test/a"])

    def test_json_mode_never_touches_stdout(self) -> None:
        # `ooda ... --json` writes its document to stdout; one log line there
        # and the caller's `jq` fails on the whole run.
        log = Logger("http", level="debug", json_mode=True)
        with captured() as (err, out):
            log.error("boom", status=500)

        self.assertEqual(out.getvalue(), "")
        self.assertEqual(len(records(err)), 1)

    def test_each_event_is_written_once(self) -> None:
        stream = RecordingStream()
        log = Logger("t", level="debug", json_mode=True)
        with mock.patch.object(sys, "stderr", stream):
            log.info("one")
            log.info("two")

        self.assertEqual(len(stream.writes), 2)
        self.assertTrue(all(w.endswith("\n") for w in stream.writes))
        self.assertTrue(all(w.count("\n") == 1 for w in stream.writes))

    def test_levels_are_prefixed_for_humans(self) -> None:
        log = Logger("t", level="debug", json_mode=False)
        with captured() as (err, _out):
            log.debug("d")
            log.info("i")
            log.warn("w")
            log.error("e")

        self.assertEqual(lines(err), ["  [t] d", "  [t] i", "! [t] w", "x [t] e"])

    def test_text_mode_without_fields_has_no_trailing_space(self) -> None:
        log = Logger("t", json_mode=False)
        with captured() as (err, _out):
            log.info("bare")

        self.assertEqual(lines(err), ["  [t] bare"])


class LoggerJsonTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.log = Logger("ingest", level="debug", json_mode=True)

    def emit(self, method: str, msg: object, /, **fields: object) -> dict:
        with captured() as (err, out):
            getattr(self.log, method)(msg, **fields)
        self.assertEqual(out.getvalue(), "")
        got = records(err)
        self.assertEqual(len(got), 1)
        return got[0]

    def test_envelope_carries_level_logger_message_and_time(self) -> None:
        record = self.emit("warn", "retrying", url="https://example.test", attempt=2)

        self.assertEqual(record["level"], "warn")
        self.assertEqual(record["logger"], "ingest")
        self.assertEqual(record["msg"], "retrying")
        self.assertEqual(record["url"], "https://example.test")
        self.assertEqual(record["attempt"], 2)
        self.assertIsInstance(record["ts"], float)
        self.assertGreater(record["ts"], 1_600_000_000)

    def test_a_newline_in_a_field_stays_inside_one_json_object(self) -> None:
        record = self.emit("error", "failed", err='HTTP 500\n{"level": "info"}\n')

        self.assertEqual(record["err"], 'HTTP 500\n{"level": "info"}\n')
        self.assertEqual(record["level"], "error")  # the forged line did not land

    def test_quotes_and_backslashes_survive_a_round_trip(self) -> None:
        record = self.emit("info", "quoted", path='C:\\tmp\\"x"', quote='he said "no"')

        self.assertEqual(record["path"], 'C:\\tmp\\"x"')
        self.assertEqual(record["quote"], 'he said "no"')

    def test_unicode_survives_a_round_trip(self) -> None:
        record = self.emit("info", "unicode", title="café \U0001f600")

        self.assertEqual(record["title"], "café \U0001f600")

    def test_non_serializable_object_becomes_its_repr(self) -> None:
        record = self.emit("info", "obj", path=Path("/tmp/x"), exc=ValueError("bad"))

        self.assertIn("/tmp/x", record["path"])
        self.assertIn("bad", record["exc"])

    def test_reference_cycle_degrades_instead_of_raising(self) -> None:
        cycle: dict[str, object] = {}
        cycle["self"] = cycle

        record = self.emit("warn", "cycle", payload=cycle)

        self.assertEqual(record["msg"], "cycle")
        self.assertIsInstance(record["payload"], str)

    def test_non_finite_floats_do_not_produce_invalid_json(self) -> None:
        # json.dumps would happily write NaN, which no strict JSON reader accepts.
        record = self.emit("info", "metrics", ratio=float("nan"), cap=float("inf"))

        self.assertEqual(record["msg"], "metrics")
        self.assertEqual(record["ratio"], "nan")
        self.assertEqual(record["cap"], "inf")

    def test_unstringifiable_dict_key_degrades_instead_of_raising(self) -> None:
        record = self.emit("info", "keys", table={(1, 2): "v"})

        self.assertEqual(record["msg"], "keys")
        self.assertIn("(1, 2)", record["table"])

    def test_a_field_whose_repr_raises_does_not_escape(self) -> None:
        class Hostile:
            def __repr__(self) -> str:
                raise RuntimeError("nope")

            def __str__(self) -> str:
                raise RuntimeError("nope")

        record = self.emit("error", "hostile", obj=Hostile())

        self.assertEqual(record["obj"], "<unrepresentable>")

    def test_fields_cannot_overwrite_the_envelope(self) -> None:
        record = self.emit(
            "error", "real", level="info", msg="fake", ts=0.0, logger="somewhere-else"
        )

        self.assertEqual(record["level"], "error")
        self.assertEqual(record["msg"], "real")
        self.assertEqual(record["logger"], "ingest")
        self.assertNotEqual(record["ts"], 0.0)
        # ...and the caller's values are kept, renamed rather than dropped.
        self.assertEqual(record["field_level"], "info")
        self.assertEqual(record["field_msg"], "fake")
        self.assertEqual(record["field_ts"], 0.0)
        self.assertEqual(record["field_logger"], "somewhere-else")

    def test_a_non_string_message_is_still_serializable(self) -> None:
        record = self.emit("error", ValueError("exploded"))  # type: ignore[arg-type]

        self.assertIn("exploded", record["msg"])

    def test_many_events_are_one_object_per_line(self) -> None:
        with captured() as (err, _out):
            for i in range(20):
                self.log.info("tick", i=i, note="line\nbreak")

        self.assertEqual(len(lines(err)), 20)
        self.assertEqual([r["i"] for r in records(err)], list(range(20)))


class LoggerTextFieldTestCase(unittest.TestCase):
    def test_newlines_in_field_values_cannot_forge_a_log_line(self) -> None:
        log = Logger("http", json_mode=False)
        with captured() as (err, _out):
            log.warn("fetch failed", err="Connection reset\nx [http] all good")

        self.assertEqual(len(lines(err)), 1)
        self.assertIn("\\n", lines(err)[0])

    def test_carriage_returns_and_tabs_are_escaped(self) -> None:
        log = Logger("t", json_mode=False)
        with captured() as (err, _out):
            log.info("v", value="a\rb\tc")

        self.assertEqual(lines(err), ["  [t] v value=a\\rb\\tc"])

    def test_a_field_whose_str_raises_does_not_escape(self) -> None:
        class Hostile:
            def __str__(self) -> str:
                raise RuntimeError("nope")

        log = Logger("t", json_mode=False)
        with captured() as (err, _out):
            log.info("hostile", obj=Hostile())

        self.assertEqual(lines(err), ["  [t] hostile obj=<unrepresentable>"])

    def test_fields_keep_call_site_order(self) -> None:
        log = Logger("t", json_mode=False)
        with captured() as (err, _out):
            log.info("ordered", z=1, a=2, m=3)

        self.assertEqual(lines(err), ["  [t] ordered z=1 a=2 m=3"])


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
