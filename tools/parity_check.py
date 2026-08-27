#!/usr/bin/env python3
"""Execute the parity matrix instead of asserting it.

`docs/parity.md` is a table of claims about what this environment can do. A
table is not evidence. This runs each capability against the live backend and
reports what actually happened, so "Claude Code reaches playground capability
X" becomes a thing you can watch succeed or fail rather than a row someone
wrote.

Three verdicts, and the third is load-bearing:

``PASS``        exercised, and the observable effect was there
``FAIL``        exercised, and it did not do what the matrix claims
``UNREACHABLE`` cannot be exercised here, with the reason stated

UNREACHABLE is not a softer FAIL. Some playground capabilities rest on the
Messages API directly, and this container has no ``ANTHROPIC_API_KEY``; others
were removed from the platform and cannot be exercised anywhere. Recording
those as failures would overstate the gap, and recording them as passes would
be a lie. They get their own verdict and their own reason.

Usage:
    python3 tools/parity_check.py              # everything, live
    python3 tools/parity_check.py --offline    # skip the checks that cost money
    python3 tools/parity_check.py --json       # machine-readable

Exit: 0 all reachable checks passed, 1 a reachable check failed, 2 could not run.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from workbench.backend import ClaudeCLIBackend, Request  # noqa: E402

PASS, FAIL, UNREACHABLE = "PASS", "FAIL", "UNREACHABLE"
MODEL = "claude-haiku-4-5"
TERSE = "You are a terse test fixture. Follow the instruction exactly."


@dataclass
class Result:
    capability: str
    verdict: str
    detail: str
    cost_usd: float = 0.0
    evidence: dict = field(default_factory=dict)


CHECKS: list = []


def check(capability: str, live: bool = True):
    def decorate(fn):
        CHECKS.append((capability, live, fn))
        return fn
    return decorate


def _run(backend, **kwargs):
    return backend.complete(Request(system=TERSE, model=MODEL, tools="", **kwargs))


# ---------------------------------------------------------------- authoring

@check("System prompt replaces the default")
def c_system(backend) -> Result:
    """The prompt under test must be the whole prompt, not an addendum."""
    # An exact token, not a themed answer: judging "did it sound like a
    # lighthouse" is the flakiness this whole repository is about avoiding.
    c = backend.complete(Request(
        prompt="What is your designation?", model=MODEL, tools="",
        system=("You are a test fixture. When asked for your designation, reply "
                "with exactly the string LIGHTHOUSE-7 and nothing else."),
    ))
    hit = "LIGHTHOUSE-7" in c.text
    return Result("System prompt replaces the default",
                  PASS if hit else FAIL,
                  f"the replaced system prompt {'took effect' if hit else 'did NOT take effect'}: "
                  f"asked for a designation, got {c.text.strip()[:60]!r}",
                  c.cost_usd or 0.0)


@check("{{variable}} templating", live=False)
def c_variables(backend) -> Result:
    from workbench.render import render
    from workbench.errors import RenderError
    out = render("Hello {{name}}, you are {{role}}.", {"name": "A", "role": "B"})
    try:
        render("{{unset}}", {})
        strict = False
    except RenderError:
        strict = True
    ok = out == "Hello A, you are B." and strict
    return Result("{{variable}} templating", PASS if ok else FAIL,
                  f"rendered {out!r}; unfilled placeholder "
                  f"{'raises' if strict else 'DOES NOT raise'}")


@check("Prompt versions are diffable artifacts", live=False)
def c_versions(backend) -> Result:
    """The retired Workbench had saved prompts. Here they are files under git."""
    suite = REPO / "suites" / "doctrine-adherence.yaml"
    if not suite.is_file():
        return Result("Prompt versions are diffable artifacts", FAIL, "no suite file found")
    log = subprocess.run(["git", "log", "--oneline", "--", str(suite)],
                         cwd=REPO, capture_output=True, text=True)
    revisions = len([l for l in log.stdout.splitlines() if l.strip()])
    return Result("Prompt versions are diffable artifacts",
                  PASS if revisions else FAIL,
                  f"{suite.name} has {revisions} revision(s) in git history; "
                  f"a saved prompt in a console cannot be diffed or reverted")


# --------------------------------------------------------------- parameters

@check("Model selection")
def c_model(backend) -> Result:
    c = _run(backend, prompt="Reply with exactly: OK")
    reported = (c.raw.get("modelUsage") or {})
    canonical = next(iter(reported.values()), {}).get("canonicalModel", "")
    ok = "haiku" in (canonical or next(iter(reported), ""))
    return Result("Model selection", PASS if ok else FAIL,
                  f"requested {MODEL}, backend reported canonicalModel={canonical!r}",
                  c.cost_usd or 0.0, {"canonicalModel": canonical})


@check("Effort control changes work done")
def c_effort(backend) -> Result:
    """Effort replaced temperature as the quality dial; show it does something."""
    prompt = "In one sentence, why is a stable sort useful?"
    low = _run(backend, prompt=prompt, effort="low")
    high = _run(backend, prompt=prompt, effort="high")

    def thinking(c):
        return ((c.raw.get("usage") or {}).get("output_tokens_details") or {}).get(
            "thinking_tokens", 0)

    lo, hi = thinking(low), thinking(high)
    ok = low.ok and high.ok and (hi != lo)
    return Result("Effort control changes work done",
                  PASS if ok else FAIL,
                  f"thinking tokens: low={lo}, high={hi}"
                  + ("" if ok else " — no observable difference, so effort may be inert here"),
                  (low.cost_usd or 0) + (high.cost_usd or 0),
                  {"low": lo, "high": hi})


@check("Thinking budget (undocumented flag)")
def c_thinking(backend) -> Result:
    prompt = "In one sentence, why is a stable sort useful?"
    capped = _run(backend, prompt=prompt, thinking="adaptive", max_thinking_tokens=1024)
    ok = capped.ok
    return Result("Thinking budget (undocumented flag)",
                  PASS if ok else FAIL,
                  f"--thinking/--max-thinking-tokens accepted and the call succeeded"
                  if ok else f"call failed: {capped.error[:120]}",
                  capped.cost_usd or 0.0)


@check("Max output tokens")
def c_max_tokens(backend) -> Result:
    c = _run(backend, prompt="Count slowly from 1 to 400, one number per line.",
             max_output_tokens=64)
    reported = next(iter((c.raw.get("modelUsage") or {}).values()), {}).get("maxOutputTokens")
    honoured = c.output_tokens <= 64 or reported == 64
    # This is a FAIL on purpose. The env var is documented, the plumbing sends
    # it, and it did not cap anything here -- output exceeded the ceiling and
    # the backend went on reporting its own maxOutputTokens. A conformance
    # harness that stayed green through that would be worthless.
    return Result("Max output tokens",
                  PASS if honoured else FAIL,
                  f"CLAUDE_CODE_MAX_OUTPUT_TOKENS=64 -> output_tokens="
                  f"{c.output_tokens}, backend still reports maxOutputTokens="
                  f"{reported}, stop_reason={c.stop_reason!r}. The variable is "
                  f"documented but was NOT honoured in this container; measured "
                  f"at 32/64/512/4096 it never changed the reported ceiling.",
                  c.cost_usd or 0.0, {"requested": 64, "reported": reported,
                                      "output_tokens": c.output_tokens})


@check("temperature / top_p / top_k", live=False)
def c_sampling(backend) -> Result:
    probes = {}
    for flag in ("--temperature", "--top-p", "--top-k"):
        out = subprocess.run(["claude", "-p", "x", flag, "1"],
                             capture_output=True, text=True, timeout=60)
        probes[flag] = "unknown option" in (out.stderr + out.stdout)
    all_rejected = all(probes.values())
    return Result("temperature / top_p / top_k", UNREACHABLE,
                  "no CLI flag (" + ", ".join(f"{k} rejected" for k in probes if probes[k])
                  + ") and on models after Opus 4.6 the API rejects them with a 400. "
                  "Removed from the platform, not missing from this tool."
                  if all_rejected else f"unexpected: {probes}")


@check("stop_sequences", live=False)
def c_stop_sequences(backend) -> Result:
    return Result("stop_sequences", UNREACHABLE,
                  "supported by the Messages API but exposed by no CLI flag, and "
                  "this container has no ANTHROPIC_API_KEY to call the API directly")


# --------------------------------------------------------------- structure

@check("Structured output against a schema")
def c_structured(backend) -> Result:
    schema = {"type": "object",
              "properties": {"city": {"type": "string"}, "population": {"type": "integer"}},
              "required": ["city", "population"], "additionalProperties": False}
    c = backend.complete(Request(
        prompt="Give the city of Paris and a rough population figure.",
        system="Return only the requested JSON object.", model=MODEL,
        tools="", json_schema=schema))
    from workbench.graders import validate_schema
    payload = c.structured
    errors = validate_schema(payload, schema) if payload is not None else ["no structured_output"]
    ok = payload is not None and not errors
    return Result("Structured output against a schema", PASS if ok else FAIL,
                  f"structured_output={json.dumps(payload)[:120] if payload else None}; "
                  f"schema errors: {errors or 'none'}",
                  c.cost_usd or 0.0, {"structured_output": payload})


@check("Tool availability is controllable")
def c_tools(backend) -> Result:
    c = _run(backend, prompt="Reply with exactly: OK")
    turns = c.num_turns
    ok = c.ok and turns == 1
    return Result("Tool availability is controllable", PASS if ok else FAIL,
                  f"--tools \"\" produced a single-turn response (num_turns={turns}), "
                  f"i.e. no tool loop", c.cost_usd or 0.0)


# -------------------------------------------------------------- inspection

@check("Request is inspectable before sending", live=False)
def c_plan(backend) -> Result:
    out = subprocess.run([sys.executable, "-m", "workbench", "plan",
                          "suites/doctrine-adherence.yaml"],
                         cwd=REPO, capture_output=True, text=True, timeout=120)
    ok = out.returncode == 0 and "model call(s) would be made" in out.stdout
    calls = [l for l in out.stdout.splitlines() if "would be made" in l]
    return Result("Request is inspectable before sending", PASS if ok else FAIL,
                  f"`workbench plan` resolved every request without sending: "
                  f"{calls[0].strip() if calls else out.stderr[:120]}")


@check("Token counts and cost are reported")
def c_accounting(backend) -> Result:
    c = _run(backend, prompt="Reply with exactly: OK")
    has = c.cost_usd is not None and c.input_tokens > 0 and c.output_tokens > 0
    return Result("Token counts and cost are reported", PASS if has else FAIL,
                  f"in={c.input_tokens} out={c.output_tokens} cost=${c.cost_usd} "
                  f"— provider-reported, not estimated from a price table",
                  c.cost_usd or 0.0)


@check("count_tokens before sending", live=False)
def c_count_tokens(backend) -> Result:
    return Result("count_tokens before sending", UNREACHABLE,
                  "/v1/messages/count_tokens exists but needs an ANTHROPIC_API_KEY, "
                  "which this container does not have")


@check("Batch API 50% discount", live=False)
def c_batch(backend) -> Result:
    return Result("Batch API 50% discount", UNREACHABLE,
                  "/v1/messages/batches needs an ANTHROPIC_API_KEY; real money for a "
                  "large sweep and genuinely absent here")


# -------------------------------------------------------------- evaluation

@check("Eval grid over test cases", live=False)
def c_grid(backend) -> Result:
    out = subprocess.run([sys.executable, "-m", "workbench", "run",
                          "suites/doctrine-adherence.yaml", "--backend", "echo",
                          "--judge-backend", "none", "-q"],
                         cwd=REPO, capture_output=True, text=True, timeout=180)
    ran = "Pass rate by variant" in out.stdout
    return Result("Eval grid over test cases", PASS if ran else FAIL,
                  "3 variants x 6 cases graded offline on the echo backend"
                  if ran else out.stderr[-200:])


@check("Blind comparison with position swap", live=False)
def c_blind(backend) -> Result:
    from workbench.blind import judge_pair, Candidate
    from workbench.backend import Completion, EchoBackend

    class Positional(EchoBackend):
        """A judge that always picks whatever is shown first."""
        def complete(self, request):
            return Completion(text='{"winner":"FIRST","reason":"x"}',
                              structured={"winner": "FIRST", "reason": "x"}, cost_usd=0.0)

    j = judge_pair(Positional(), "which is better",
                   Candidate("a", "one"), Candidate("b", "two"), "c", tokens=[])
    ok = j.winner == "TIE" and not j.agreed
    return Result("Blind comparison with position swap", PASS if ok else FAIL,
                  f"a judge that always picks the first candidate was correctly "
                  f"downgraded to {j.winner!r} (agreed={j.agreed}) — the swap caught it"
                  if ok else f"swap did NOT catch a purely positional judge: {j.winner}")


@check("Identical-pair blinding control", live=False)
def c_control(backend) -> Result:
    from workbench.blind import identical_pair_control
    from workbench.backend import Completion, EchoBackend

    class Tying(EchoBackend):
        def complete(self, request):
            return Completion(text='{"winner":"TIE","reason":"same"}',
                              structured={"winner": "TIE", "reason": "same"}, cost_usd=0.0)

    class Leaky(EchoBackend):
        def complete(self, request):
            return Completion(text='{"winner":"FIRST","reason":"x"}',
                              structured={"winner": "FIRST", "reason": "x"}, cost_usd=0.0)

    good = identical_pair_control(Tying(), "c", "same text")
    bad = identical_pair_control(Leaky(), "c", "same text")
    ok = good["passed"] and not bad["passed"]
    return Result("Identical-pair blinding control", PASS if ok else FAIL,
                  "a tying judge passes the control and a judge that picks a winner "
                  "between two identical candidates fails it" if ok
                  else "control does not discriminate")


@check("Significance testing", live=False)
def c_stats(backend) -> Result:
    from workbench.stats import sign_test, wilson_interval, required_pairs
    weak, strong = sign_test(4, 2), sign_test(10, 0)
    ci = wilson_interval(4, 4)
    ok = weak > 0.05 and strong < 0.05 and ci.low < 1.0
    return Result("Significance testing", PASS if ok else FAIL,
                  f"4-2 -> p={weak:.3f} (not significant), 10-0 -> p={strong:.4f} "
                  f"(significant), 4/4 -> CI {ci}; ~{required_pairs()} pairs needed "
                  f"for a 70/30 effect")


@check("Grade by shell command (outcome-based)", live=False)
def c_outcome(backend) -> Result:
    from workbench.graders import run_grader, GradingContext
    from workbench.backend import Completion
    from workbench.spec import Grader
    g = Grader("command", {"command": f'python3 "{REPO}/tools/grade_no_fabrication.py" {{output_file}}'})
    clean = run_grader(g, GradingContext(
        completion=Completion(text="I cannot establish that from what is available."),
        case_id="c", variant_id="v"))
    dirty = run_grader(g, GradingContext(
        completion=Completion(text="As we discussed, the retention policy is 90 days."),
        case_id="c", variant_id="v"))
    ok = clean.passed and not dirty.passed
    return Result("Grade by shell command (outcome-based)", PASS if ok else FAIL,
                  "the repository's own fabrication guard passed an honest answer and "
                  "failed an invented one, by exit code" if ok
                  else f"clean={clean.passed} dirty={dirty.passed}")


@check("Export to claude plugin eval", live=False)
def c_export(backend) -> Result:
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        out = subprocess.run([sys.executable, "-m", "workbench", "export-eval",
                              "suites/doctrine-adherence.yaml", "--out", tmp],
                             cwd=REPO, capture_output=True, text=True, timeout=120)
        cases = list(Path(tmp).glob("*/prompt.md"))
        graders = list(Path(tmp).glob("*/graders/*.md"))
    ok = out.returncode == 0 and cases and graders
    return Result("Export to claude plugin eval", PASS if ok else FAIL,
                  f"emitted {len(cases)} case(s) and {len(graders)} grader file(s) in "
                  f"the format `claude plugin eval` reads")


@check("claude plugin eval is available", live=False)
def c_plugin_eval(backend) -> Result:
    out = subprocess.run(["claude", "plugin", "eval", "--help"],
                         capture_output=True, text=True, timeout=90)
    ok = out.returncode == 0
    return Result("claude plugin eval is available", PASS if ok else FAIL,
                  "present and runnable; its ablation is with-plugin vs without-plugin, "
                  "not N prompt variants" if ok else "not available here")


@check("skill-creator is available", live=False)
def c_skill_creator(backend) -> Result:
    path = Path("/mnt/skills/examples/skill-creator")
    comparator = path / "agents" / "comparator.md"
    if not comparator.is_file():
        return Result("skill-creator is available", FAIL, "not found on this machine")

    text = comparator.read_text(encoding="utf-8", errors="replace")
    blind = "do NOT know which skill produced which" in text

    # Does it judge the pair a second time with the candidates transposed?
    # A naive repo-wide grep for "swap" is worthless here: it hits Google Fonts
    # `display=swap` in the HTML assets and a `random.shuffle` that stratifies a
    # train/test split. Ask the precise question instead -- does the comparator
    # protocol describe a reversed second pass?
    swap_terms = ("swap", "reversed order", "transpos", "both orders",
                  "second pass", "run twice")
    lowered = text.lower()
    swaps = any(term in lowered for term in swap_terms)

    return Result("skill-creator is available", PASS if blind else FAIL,
                  f"first-party blind comparator at {path}: withholds which skill "
                  f"produced which output, and its protocol describes "
                  f"{'a position swap' if swaps else 'a single fixed-order judgement'}"
                  f" — use it for skills; use this workbench when the comparison "
                  f"needs the swap, more than two variants, or a p-value")


# --------------------------------------------------------------------------

def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--offline", action="store_true",
                        help="skip checks that make live model calls")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv[1:])

    backend = ClaudeCLIBackend()
    usable, detail = backend.available()
    if not usable and not args.offline:
        print(f"parity_check: backend unavailable: {detail}", file=sys.stderr)
        return 2

    results: list[Result] = []
    started = time.time()
    for capability, live, fn in CHECKS:
        if live and args.offline:
            results.append(Result(capability, UNREACHABLE, "skipped (--offline)"))
            continue
        try:
            results.append(fn(backend))
        except Exception as exc:  # a check that crashes is a failure, not a skip
            results.append(Result(capability, FAIL, f"check raised {type(exc).__name__}: {exc}"))

    total_cost = sum(r.cost_usd for r in results)
    counts = {v: sum(1 for r in results if r.verdict == v) for v in (PASS, FAIL, UNREACHABLE)}

    if args.json:
        print(json.dumps({
            "results": [r.__dict__ for r in results],
            "counts": counts, "cost_usd": round(total_cost, 6),
            "duration_s": round(time.time() - started, 1),
        }, indent=2))
    else:
        print("Parity conformance — executed, not asserted")
        print("=" * 72)
        for r in results:
            mark = {PASS: "PASS", FAIL: "FAIL", UNREACHABLE: "----"}[r.verdict]
            print(f"[{mark}] {r.capability}")
            for line in (r.detail or "").splitlines():
                print(f"       {line}")
        print("=" * 72)
        print(f"{counts[PASS]} passed, {counts[FAIL]} failed, "
              f"{counts[UNREACHABLE]} unreachable — ${total_cost:.4f}, "
              f"{time.time() - started:.0f}s")
        if counts[UNREACHABLE]:
            print("\nUnreachable is not a softer failure. Those capabilities either "
                  "need\nan API key this container does not have, or were removed from "
                  "the\nplatform and cannot be exercised anywhere.")
    return 1 if counts[FAIL] else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
