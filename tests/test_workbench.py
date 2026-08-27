#!/usr/bin/env python3
"""Tests for the workbench.

Two things are being proved here, and the second is the one that matters.

First, that the machinery works: templates render, suites load, graders grade,
statistics compute.

Second, that every guard **rejects** something. A strict loader that has never
refused a malformed suite, a blinder that has never been caught leaking a
model name, a judge protocol that has never turned a position-flip into a tie
-- none of those are guards, they are hopes with test coverage. So each case
below names the specific thing being refused.

The whole file runs on the echo backend: offline, free, deterministic. Running
the tests must never depend on a model's mood or cost anyone money.

Run: python3 tests/test_workbench.py
"""

import json
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from workbench.backend import Completion, EchoBackend, Request  # noqa: E402
from workbench.blind import (  # noqa: E402
    Candidate, blind_text, identity_tokens, judge_pair, position_bias_rate, seal,
)
from workbench.errors import RenderError, SpecError  # noqa: E402
from workbench.graders import (  # noqa: E402
    DETERMINISTIC, MODEL, GradingContext, describe_registry, run_grader,
    unsupported_schema_keys, validate_schema,
)
from workbench.render import render, variables_in  # noqa: E402
from workbench.report import markdown  # noqa: E402
from workbench.runner import execute  # noqa: E402
from workbench.spec import Grader, load_suite  # noqa: E402
from workbench.stats import (  # noqa: E402
    bradley_terry, required_pairs, sign_test, summarise_pairwise, wilson_interval,
)

FAILURES: list[str] = []


def check(name: str, condition: bool, detail: str = "") -> None:
    if condition:
        print(f"  ok   {name}")
    else:
        print(f"  FAIL {name} {detail}")
        FAILURES.append(name)


def rejects(name: str, fn, exception=Exception) -> None:
    """Assert that ``fn`` refuses. A guard is real once you watch it say no."""
    try:
        fn()
    except exception as exc:
        print(f"  ok   {name}  ({type(exc).__name__})")
        return
    print(f"  FAIL {name}: accepted what it should have refused")
    FAILURES.append(name)


def ctx_for(text: str, **kwargs) -> GradingContext:
    completion = Completion(
        text=text, cost_usd=kwargs.pop("cost", 0.001),
        duration_ms=kwargs.pop("duration_ms", 100),
        output_tokens=kwargs.pop("output_tokens", 10),
        structured=kwargs.pop("structured", None),
    )
    return GradingContext(completion=completion, case_id="c", variant_id="v", **kwargs)


def write_suite(body: str) -> Path:
    directory = Path(tempfile.mkdtemp(prefix="wb-suite-"))
    path = directory / "suite.yaml"
    path.write_text(body, encoding="utf-8")
    return path


# --------------------------------------------------------------------------

def test_render() -> None:
    print("\ntemplating")
    check("substitutes", render("hi {{name}}", {"name": "there"}) == "hi there")
    check("repeats a variable",
          render("{{x}}-{{x}}", {"x": "a"}) == "a-a")
    check("finds names in order", variables_in("{{b}} {{a}} {{b}}") == ["b", "a"])
    rejects("an unfilled placeholder is refused, not blanked",
            lambda: render("{{missing}}", {}), RenderError)

    # The specific danger: a missing variable rendering to "" produces a
    # prompt that still looks fine and evaluates to nonsense.
    try:
        render("Answer: {{expected}}", {})
    except RenderError as exc:
        check("the error names the missing variable", "expected" in str(exc))


def test_spec() -> None:
    print("\nsuite loading")
    path = write_suite("""
name: t
vars: {who: world}
variants:
  - id: a
  - id: b
    system: 'You are {{who}}.'
cases:
  - id: c1
    prompt: 'hello {{who}}'
    graders: [json_valid, {type: regex, pattern: 'h'}]
""")
    suite = load_suite(path)
    check("loads variants and cases",
          [v.id for v in suite.variants] == ["a", "b"] and len(suite.cases) == 1)
    check("grader shorthand expands", suite.cases[0].graders[0].type == "json_valid")

    rejects("a mistyped key is refused rather than ignored",
            lambda: load_suite(write_suite(
                "name: t\nvariants: [{id: a, temprature: 0.5}]\ncases: [{id: c, prompt: p}]"
            )), SpecError)
    rejects("duplicate variant ids are refused",
            lambda: load_suite(write_suite(
                "name: t\nvariants: [{id: a}, {id: a}]\ncases: [{id: c, prompt: p}]"
            )), SpecError)
    rejects("duplicate case ids are refused",
            lambda: load_suite(write_suite(
                "name: t\nvariants: [{id: a}]\ncases: [{id: c, prompt: p}, {id: c, prompt: q}]"
            )), SpecError)
    rejects("a case with no prompt is refused",
            lambda: load_suite(write_suite(
                "name: t\nvariants: [{id: a}]\ncases: [{id: c}]"
            )), SpecError)
    rejects("a suite with no variants is refused",
            lambda: load_suite(write_suite("name: t\ncases: [{id: c, prompt: p}]")), SpecError)
    rejects("an unknown mode is refused",
            lambda: load_suite(write_suite(
                "name: t\nvariants: [{id: a, mode: telepathy}]\ncases: [{id: c, prompt: p}]"
            )), SpecError)
    rejects("a missing system_file is refused",
            lambda: load_suite(write_suite(
                "name: t\nvariants: [{id: a, system_file: nope.md}]\ncases: [{id: c, prompt: p}]"
            )), SpecError)


def test_graders() -> None:
    print("\ngraders -- each must pass the right thing and fail the wrong one")

    cases = [
        ("equals", {"value": "yes"}, "yes", "no"),
        ("contains", {"value": "src"}, "a [src:X] b", "nothing here"),
        ("not_contains", {"value": "as we discussed"}, "clean text", "as we discussed, x"),
        ("regex", {"pattern": r"\[src:[A-Z0-9-]+\]"}, "a [src:AB-1]", "no tag"),
        ("word_count", {"min": 2, "max": 4}, "one two three", "one"),
        ("contains_all", {"values": ["a", "b"]}, "a and b", "only a"),
        ("contains_any", {"values": ["x", "y"]}, "has y", "neither"),
        ("json_valid", {}, '{"a": 1}', "not json"),
        ("cost_under", {"usd": 0.01}, "x", None),
        ("no_error", {}, "some text", ""),
    ]
    for gtype, config, good, bad in cases:
        g = Grader(gtype, config)
        good_v = run_grader(g, ctx_for(good))
        check(f"{gtype} passes valid input", good_v.passed, good_v.detail)
        if bad is not None:
            bad_v = run_grader(g, ctx_for(bad))
            check(f"{gtype} FAILS invalid input", not bad_v.passed, bad_v.detail)

    over = run_grader(Grader("cost_under", {"usd": 0.0001}), ctx_for("x", cost=0.5))
    check("cost_under FAILS when over budget", not over.passed)

    slow = run_grader(Grader("latency_under", {"ms": 10}), ctx_for("x", duration_ms=9999))
    check("latency_under FAILS when slow", not slow.passed)

    print("\n  regex match modes")
    for mode, text, expected in [
        ("absent", "clean", True), ("absent", "x x", False),
        ("count:2", "x x", True), ("count:2", "x", False),
        ("min:1", "x", True), ("min:3", "x", False),
    ]:
        v = run_grader(Grader("regex", {"pattern": "x", "match": mode}), ctx_for(text))
        check(f"regex match={mode} on {text!r}", v.passed is expected, v.detail)

    print("\n  a broken grader must score zero, never a silent pass")
    broken = run_grader(Grader("regex", {"pattern": "x"}), ctx_for("x"))
    check("valid regex still works", broken.passed)
    bad_config = run_grader(Grader("word_count", {"min": "not-a-number"}), ctx_for("a b"))
    check("a grader that raises is recorded as a failure",
          not bad_config.passed and "raised" in bad_config.detail, bad_config.detail)

    print("\n  the command grader -- outcome-based, exit code decides")
    ok = run_grader(Grader("command", {"command": "grep -q hello {output_file}"}),
                    ctx_for("hello world"))
    check("command grader passes on exit 0", ok.passed, ok.detail)
    no = run_grader(Grader("command", {"command": "grep -q absent {output_file}"}),
                    ctx_for("hello world"))
    check("command grader FAILS on non-zero exit", not no.passed, no.detail)

    print("\n  unknown grader types are refused, not skipped")
    rejects("an unknown grader type is refused",
            lambda: run_grader(Grader("vibes", {}), ctx_for("x")))
    rejects("a judge with no backend is refused rather than scored as a pass",
            lambda: run_grader(Grader("judge", {"criteria": "is it good"}), ctx_for("x")))


def test_schema_validation() -> None:
    print("\nJSON schema subset")
    schema = {
        "type": "object",
        "properties": {"n": {"type": "integer", "minimum": 1},
                       "s": {"type": "string", "enum": ["a", "b"]}},
        "required": ["n", "s"],
        "additionalProperties": False,
    }
    check("valid object passes", validate_schema({"n": 2, "s": "a"}, schema) == [])
    check("missing required is caught",
          any("missing required" in e for e in validate_schema({"n": 1}, schema)))
    check("wrong type is caught",
          any("expected type" in e for e in validate_schema({"n": "x", "s": "a"}, schema)))
    check("enum violation is caught",
          any("enum" in e for e in validate_schema({"n": 1, "s": "z"}, schema)))
    check("minimum is enforced",
          any("minimum" in e for e in validate_schema({"n": 0, "s": "a"}, schema)))
    check("additionalProperties false is enforced",
          any("unexpected" in e for e in validate_schema({"n": 1, "s": "a", "x": 1}, schema)))
    check("booleans are not integers",
          any("expected type" in e for e in validate_schema({"n": True, "s": "a"}, schema)))

    # The honest part: say what is NOT enforced rather than implying it is.
    unsupported = unsupported_schema_keys({"type": "object", "oneOf": [], "$ref": "#/x"})
    check("unsupported keywords are reported, not silently ignored",
          "$.oneOf" in unsupported and "$.$ref" in unsupported, str(unsupported))


def test_blinding() -> None:
    print("\nblinding -- the judge must not be able to tell which arm is which")
    tokens = identity_tokens(
        ["with-doctrine", "control"], ["claude-haiku-4-5-20251001"], ["workbench"]
    )
    leaky = ("As claude-haiku-4-5 running the with-doctrine configuration in "
             "workbench, I would say the control arm is worse.")
    blinded, count = blind_text(leaky, tokens)
    check("the model id is removed", "haiku" not in blinded.lower(), blinded)
    check("the variant id is removed", "with-doctrine" not in blinded, blinded)
    check("the other variant id is removed", "control" not in blinded.lower(), blinded)
    check("extra redactions are honoured", "workbench" not in blinded.lower(), blinded)
    check("the number of redactions is reported", count >= 4, str(count))

    check("redaction is case-insensitive",
          "[REDACTED]" in blind_text("WITH-DOCTRINE", tokens)[0])
    check("clean text is left alone", blind_text("plain answer", tokens) == ("plain answer", 0))

    cands = [Candidate("a", "x"), Candidate("b", "y"), Candidate("c", "z")]
    first = seal(cands, "seed")[1]
    check("sealing is deterministic for a seed", first == seal(cands, "seed")[1])
    check("sealing hides identity behind positions", set(first) == {"C1", "C2", "C3"})


class _ScriptedJudge(EchoBackend):
    """A judge whose verdicts are dictated by the test, in call order."""

    def __init__(self, verdicts: list[str]) -> None:
        self.verdicts = list(verdicts)
        self.seen: list[str] = []

    def complete(self, request: Request) -> Completion:
        self.seen.append(request.prompt)
        verdict = self.verdicts.pop(0)
        return Completion(
            text=json.dumps({"winner": verdict, "reason": "scripted"}),
            structured={"winner": verdict, "reason": "scripted"},
            cost_usd=0.0, backend="scripted",
        )


def test_position_swap() -> None:
    print("\nposition swap -- the mechanism that separates a result from a vibe")
    a, b = Candidate("alpha", "answer one"), Candidate("beta", "answer two")

    # Consistent: alpha is picked whichever position it occupies.
    judge = _ScriptedJudge(["FIRST", "SECOND"])
    consistent = judge_pair(judge, "which is better", a, b, "c1", tokens=[])
    check("a win that survives the swap is recorded as a win",
          consistent.winner == "alpha" and consistent.agreed, consistent.winner)

    # Inconsistent: the judge picks whatever is presented first.
    judge = _ScriptedJudge(["FIRST", "FIRST"])
    flipped = judge_pair(judge, "which is better", a, b, "c1", tokens=[])
    check("a win that flips with the order is downgraded to a tie",
          flipped.winner == "TIE" and not flipped.agreed, flipped.winner)

    # Both orders are actually run, with the candidates transposed.
    check("the pair is judged exactly twice", len(judge.seen) == 2)
    first_prompt, second_prompt = judge.seen
    check("the second presentation reverses the order",
          first_prompt.index("answer one") < first_prompt.index("answer two")
          and second_prompt.index("answer two") < second_prompt.index("answer one"))

    judge = _ScriptedJudge(["TIE", "TIE"])
    tie = judge_pair(judge, "c", a, b, "c1", tokens=[])
    check("an agreed tie stays a tie", tie.winner == "TIE" and tie.agreed)

    rate = position_bias_rate([consistent, flipped, tie])
    check("position-bias rate counts only the disagreements",
          abs(rate - 1 / 3) < 1e-9, str(rate))


def test_statistics() -> None:
    print("\nstatistics -- small samples must not be allowed to look decisive")
    check("4 wins to 2 losses is NOT significant", sign_test(4, 2) > 0.05,
          str(sign_test(4, 2)))
    check("10 wins to 0 losses IS significant", sign_test(10, 0) < 0.05,
          str(sign_test(10, 0)))
    check("no decided pairs yields p = 1", sign_test(0, 0) == 1.0)
    check("the test is symmetric", sign_test(2, 7) == sign_test(7, 2))

    interval = wilson_interval(4, 4)
    check("4/4 does not claim certainty", interval.low < 1.0, str(interval))
    check("0 trials yields the full interval", str(wilson_interval(0, 0)) == "[0.000, 1.000]")

    check("a real effect needs a real sample", required_pairs() > 20, str(required_pairs()))

    strengths = bradley_terry([("a", "b"), ("a", "b"), ("a", "c"), ("b", "c"), ("b", "c")])
    check("Bradley-Terry ranks a above b above c",
          strengths["a"] > strengths["b"] > strengths["c"], str(strengths))
    check("strengths are shares summing to one",
          abs(sum(strengths.values()) - 1.0) < 1e-6)
    check("an undefeated variant does not produce an infinity",
          all(v == v and v != float("inf") for v in
              bradley_terry([("a", "b"), ("a", "b")]).values()))

    summary = summarise_pairwise(["a", "a", "TIE", "b", "a", "a"], "a", "b")
    check("ties are excluded from the significance test", summary["decided"] == 5)
    check("ties count as half in the headline rate",
          abs(summary["win_rate_a_ties_as_half"] - 0.75) < 1e-9)
    check("a 4-1 split is reported as not significant",
          summary["significant_at_0.05"] is False, str(summary["p_value_sign_test"]))


def test_end_to_end() -> None:
    print("\nend to end on the echo backend -- free, offline, deterministic")
    path = write_suite("""
name: e2e
description: proves the loop closes
repeats: 1
variants:
  - id: good
    prompt_suffix: ' [[echo: {"answer": "yes"}]]'
  - id: bad
    prompt_suffix: ' [[echo: nonsense]]'
cases:
  - id: must-be-json
    prompt: 'produce json'
    graders:
      - json_valid
      - {type: json_path, path: answer, equals: 'yes'}
""")
    suite = load_suite(path)
    result = execute(suite, EchoBackend(), report=lambda m: None)
    check("every variant ran every case", len(result.runs) == 2)
    good = [r for r in result.runs if r.variant_id == "good"][0]
    bad = [r for r in result.runs if r.variant_id == "bad"][0]
    check("the conforming variant passes", good.passed, good.output)
    check("the non-conforming variant FAILS", not bad.passed, bad.output)
    check("the echo backend reports zero cost", result.cost_usd == 0.0)

    rendered = markdown(result)
    check("the report names both variants",
          "`good`" in rendered and "`bad`" in rendered)
    check("the report splits verdicts by grader kind",
          "Where the verdicts came from" in rendered)
    check("the report states what it did not establish",
          "did not establish" in rendered)
    check("the report says costs are backend-reported",
          "not estimated" in rendered)

    print("\n  advisory graders report but must not gate")
    path = write_suite("""
name: advisory
variants: [{id: v, prompt_suffix: ' [[echo: hello]]'}]
cases:
  - id: c
    prompt: 'x'
    graders:
      - {type: contains, value: hello}
      - {type: contains, value: absent-thing, advisory: true}
""")
    result = execute(load_suite(path), EchoBackend(), report=lambda m: None)
    run = result.runs[0]
    check("a failing advisory grader does not fail the run", run.passed)
    check("but it is still recorded", any(not v.passed for v in run.verdicts))


def test_registry_kinds() -> None:
    print("\ngrader taxonomy")
    kinds = dict(describe_registry())
    check("regex is deterministic", kinds["regex"] == DETERMINISTIC)
    check("judge is marked as a model opinion", kinds["judge"] == MODEL)
    check("command is environmental", kinds["command"] == "environmental")
    check("every grader declares a kind",
          all(k in ("deterministic", "environmental", "model") for k in kinds.values()))


def main() -> int:
    test_render()
    test_spec()
    test_graders()
    test_schema_validation()
    test_blinding()
    test_position_swap()
    test_statistics()
    test_end_to_end()
    test_registry_kinds()

    print()
    if FAILURES:
        print(f"{len(FAILURES)} case(s) failed: {', '.join(FAILURES)}")
        return 1
    print("all cases passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
