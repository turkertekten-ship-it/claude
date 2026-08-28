#!/usr/bin/env python3
"""Tests for the differential token counter.

The counter's live proof is `--selfcheck`, which spends real calls on real
probes. These tests are the offline half: they run in `tests/run_all.sh`, cost
nothing, and cover the parts that must hold regardless of what the network
says -- the arithmetic, and every way a probe can fail.

A guard is only real once it has been watched rejecting something, so the
failure cases here are the point. A counter that returned plausible numbers
when the CLI was missing, or when the baseline drifted, would be worse than no
counter at all: it would put fabricated token counts into a repository whose
entire purpose is not doing that.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))

import count_tokens as ct  # noqa: E402

# Held from import time. The earlier cases monkeypatch `ct.probe`, and the first
# draft of this file then "tested" the real probe against a stand-in that was
# still installed -- both of its cases failed, which is the only reason the
# substitution was noticed. Restore explicitly rather than relying on order.
REAL_PROBE = ct.probe

FAILURES: list[str] = []


def check(name: str, condition: bool, detail: str = "") -> None:
    if condition:
        print(f"  ok   {name}")
    else:
        print(f"  FAIL {name} {detail}")
        FAILURES.append(name)


class FakeProbe:
    """A tokenizer stand-in: baseline plus one token per whitespace word."""

    def __init__(self, baseline: int = 231) -> None:
        self.baseline = baseline
        self.calls: list[str] = []

    def __call__(self, system: str, model: str = ct.MODEL) -> int:
        self.calls.append(system)
        return self.baseline + len(system.split())


def arithmetic_cases() -> None:
    print("arithmetic")
    fake = FakeProbe()
    ct.probe = fake
    counter = ct.Counter()

    check("baseline is calibrated, not hardcoded", counter.baseline == 231)
    check("count subtracts the baseline", counter.count("a b c") == 3)
    check("counting is additive under this probe",
          counter.count("a b") + counter.count("c d") == counter.count("a b c d"))

    before = len(fake.calls)
    check("empty text returns zero", counter.count("") == 0)
    check("empty text spends no probe", len(fake.calls) == before)

    # A baseline of 231 with a 231-token frame must not report the frame as
    # content. This is the specific way a differential counter goes wrong.
    check("text is never charged the frame", counter.count("one") == 1)


def recalibration_case() -> None:
    """A CLI upgrade that moves the frame must not corrupt counts silently."""
    print("recalibration")
    moved = FakeProbe(baseline=4096)
    ct.probe = moved
    counter = ct.Counter()
    check("a different frame is absorbed by calibration",
          counter.baseline == 4096 and counter.count("a b c") == 3,
          f"baseline={counter.baseline}")


def failure_cases() -> None:
    """Every probe failure must raise, never return a number."""
    print("failure modes")

    def raises(name: str, fn) -> None:
        ct.probe = fn
        try:
            ct.Counter()
        except ct.ProbeError:
            check(name, True)
        except Exception as exc:  # noqa: BLE001
            check(name, False, f"raised {type(exc).__name__}, wanted ProbeError")
        else:
            check(name, False, "returned a count instead of raising")

    def missing_cli(system: str, model: str = ct.MODEL) -> int:
        raise ct.ProbeError("the `claude` CLI is not on PATH")

    def timed_out(system: str, model: str = ct.MODEL) -> int:
        raise ct.ProbeError("probe timed out after 120s")

    def no_usage(system: str, model: str = ct.MODEL) -> int:
        raise ct.ProbeError("no usage.input_tokens in the response: ['result']")

    raises("a missing CLI raises rather than guessing", missing_cli)
    raises("a timeout raises rather than guessing", timed_out)
    raises("a response without usage raises rather than guessing", no_usage)


def real_probe_parsing() -> None:
    """The real probe must reject bad output instead of inventing a count."""
    print("real probe, fed bad output")
    ct.probe = REAL_PROBE
    original = subprocess.run

    def fake_run(cmd, **kwargs):
        class P:
            returncode = 0
            stdout = "not json at all"
            stderr = ""
        return P()

    subprocess.run = fake_run
    try:
        ct.probe("x")
    except ct.ProbeError as exc:
        check("non-JSON output raises", "non-JSON" in str(exc))
    else:
        check("non-JSON output raises", False, "returned a count")
    finally:
        subprocess.run = original

    def error_run(cmd, **kwargs):
        class P:
            returncode = 0
            stdout = '{"is_error": true, "result": "credit balance too low"}'
            stderr = ""
        return P()

    subprocess.run = error_run
    try:
        ct.probe("x")
    except ct.ProbeError as exc:
        check("a CLI-reported error raises", "credit balance" in str(exc))
    else:
        check("a CLI-reported error raises", False, "returned a count")
    finally:
        subprocess.run = original


def main() -> int:
    print("differential token counter")
    arithmetic_cases()
    recalibration_case()
    failure_cases()
    real_probe_parsing()
    print()
    if FAILURES:
        print(f"FAILED: {len(FAILURES)} case(s): {', '.join(FAILURES)}")
        return 1
    print("all cases passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
