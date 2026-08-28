#!/usr/bin/env python3
"""Count tokens with Anthropic's own tokenizer, without an API key.

The `/v1/messages/count_tokens` endpoint needs a credential this container does
not have, and every documented path to one was checked and found closed. So
`docs/parity.md` carried token counting as unreachable, and the fabrication
suite contains a trap -- `spec-05`, "how many tokens does the operating prompt
consume?" -- whose correct answer was that nobody here could know.

That turns out to have been true of the endpoint and false of the capability.
`claude -p --output-format json` reports `usage.input_tokens` for the request it
just sent, counted by the same tokenizer the model uses. Replacing the system
prompt with the text of interest and subtracting a calibrated empty baseline
gives the token count of that text by difference.

**Why this is a measurement and not an estimate.** Three properties were checked
before the tool was written, not assumed:

- *Determinism.* The empty baseline returned 231 on three consecutive probes,
  identical every time.
- *Additivity.* Two 11-token strings measured 11 and 11 alone, and 22
  concatenated. A tokenizer that did not really tokenize would not do that.
- *Isolation.* `--tools "" --setting-sources ""` strips project settings and
  tool schemas, so the baseline is a fixed frame rather than whatever the
  working directory happens to contain. Without it the frame was 3632 tokens
  and would drift with the repository.

**What it is not.** It is not the count_tokens endpoint, and it does not claim
to be: the endpoint counts a full Messages request with its own framing, while
this counts text in the system-prompt slot. The two agree on the text and need
not agree on the envelope. Each measurement is a real, billed model call --
cheap, around $0.0002, but not free, and it needs the network.

The baseline is re-measured on every invocation rather than hardcoded, because a
CLI upgrade that changed the frame would otherwise silently corrupt every count.

Usage:
    python3 tools/count_tokens.py FILE...
    python3 tools/count_tokens.py --text "some string"
    echo hello | python3 tools/count_tokens.py -
    python3 tools/count_tokens.py --selfcheck

Exit: 0 counted, 1 a check failed, 2 could not run.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

MODEL = "claude-haiku-4-5"
TIMEOUT_S = 120

# Guards on the differential method itself. If the tokenizer stopped being
# additive, or the frame stopped being fixed, every count below would be wrong
# in a way no amount of care in the caller would catch.
ADDITIVITY_A = "The quick brown fox jumps over the lazy dog."
ADDITIVITY_B = "Pack my box with five dozen liquor jugs."


class ProbeError(RuntimeError):
    pass


def probe(system: str, model: str = MODEL) -> int:
    """Return `usage.input_tokens` for a minimal request carrying `system`."""
    cmd = [
        "claude", "-p", "x",
        "--model", model,
        "--output-format", "json",
        "--tools", "",
        "--setting-sources", "",
        "--system-prompt", system,
    ]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=TIMEOUT_S)
    except FileNotFoundError as exc:
        raise ProbeError("the `claude` CLI is not on PATH") from exc
    except subprocess.TimeoutExpired as exc:
        raise ProbeError(f"probe timed out after {TIMEOUT_S}s") from exc
    if proc.returncode != 0:
        raise ProbeError(f"claude exited {proc.returncode}: {proc.stderr.strip()[:400]}")
    try:
        payload = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise ProbeError(f"non-JSON output: {proc.stdout[:200]!r}") from exc
    if payload.get("is_error"):
        raise ProbeError(f"claude reported an error: {payload.get('result', '')[:400]}")
    try:
        return int(payload["usage"]["input_tokens"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ProbeError(f"no usage.input_tokens in the response: {sorted(payload)}") from exc


class Counter:
    """Differential token counter. Calibrates its baseline once per instance."""

    def __init__(self, model: str = MODEL) -> None:
        self.model = model
        self.baseline = probe("", model)
        self.calls = 1

    def count(self, text: str) -> int:
        if not text:
            return 0
        self.calls += 1
        return probe(text, self.model) - self.baseline


def selfcheck(model: str = MODEL) -> int:
    """Prove the method before trusting any number it produces."""
    failures = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  {'ok  ' if ok else 'FAIL'} {name}" + (f"  {detail}" if detail else ""))
        if not ok:
            failures.append(name)

    print(f"differential token counting — selfcheck ({model})")
    try:
        first = probe("", model)
        second = probe("", model)
    except ProbeError as exc:
        print(f"  could not run: {exc}", file=sys.stderr)
        return 2

    check("empty baseline is deterministic", first == second, f"{first} vs {second}")
    if first != second:
        print("\nA drifting baseline makes every differential count wrong.",
              file=sys.stderr)
        return 1

    counter = Counter(model)
    try:
        a = counter.count(ADDITIVITY_A)
        b = counter.count(ADDITIVITY_B)
        ab = counter.count(ADDITIVITY_A + ADDITIVITY_B)
    except ProbeError as exc:
        print(f"  could not run: {exc}", file=sys.stderr)
        return 2

    check("counts are positive", a > 0 and b > 0, f"a={a} b={b}")
    check("concatenation is additive", ab == a + b, f"{a}+{b}={a + b} vs {ab}")
    check("empty text costs nothing and no call", counter.count("") == 0)

    print()
    if failures:
        print(f"FAILED: {', '.join(failures)}")
        print("The differential method does not hold here. Do not use the counts.")
        return 1
    print(f"method holds — baseline {counter.baseline} tokens, "
          f"{counter.calls} probe(s) spent")
    return 0


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        prog="count_tokens.py",
        description="Count tokens with the model's own tokenizer, via the CLI.")
    parser.add_argument("paths", nargs="*", metavar="FILE",
                        help="files to count; `-` reads stdin")
    parser.add_argument("--text", help="count this string instead of a file")
    parser.add_argument("--model", default=MODEL)
    parser.add_argument("--selfcheck", action="store_true",
                        help="prove determinism and additivity, then exit")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv[1:])

    if args.selfcheck:
        return selfcheck(args.model)

    items: list[tuple[str, str]] = []
    if args.text is not None:
        items.append(("--text", args.text))
    for path in args.paths:
        if path == "-":
            items.append(("<stdin>", sys.stdin.read()))
            continue
        p = Path(path)
        if not p.exists():
            print(f"no such file: {path}", file=sys.stderr)
            return 2
        items.append((path, p.read_text(encoding="utf-8", errors="replace")))

    if not items:
        parser.print_help(sys.stderr)
        return 2

    try:
        counter = Counter(args.model)
        results = [(name, counter.count(text)) for name, text in items]
    except ProbeError as exc:
        print(f"could not run: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps({
            "model": args.model,
            "baseline_tokens": counter.baseline,
            "probes": counter.calls,
            "counts": {name: n for name, n in results},
        }, indent=2))
        return 0

    width = max(len(name) for name, _ in results)
    for name, n in results:
        print(f"{name:<{width}}  {n:>7,} tokens")
    if len(results) > 1:
        print(f"{'total':<{width}}  {sum(n for _, n in results):>7,} tokens")
    print(f"\nmeasured by difference against a {counter.baseline}-token baseline "
          f"on {args.model}; {counter.calls} billed probe(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
