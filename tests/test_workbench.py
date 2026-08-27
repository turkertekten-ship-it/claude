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
    Candidate, blind_text, identical_pair_control, identity_tokens, judge_pair,
    length_summary, position_bias_rate, same_family, seal,
)
from workbench.errors import RenderError, SpecError  # noqa: E402
from workbench.graders import (  # noqa: E402
    DETERMINISTIC, MODEL, GradingContext, Verdict, describe_registry, run_grader,
    unsupported_schema_keys, validate_schema,
)
from workbench.render import render, variables_in  # noqa: E402
from workbench.report import markdown  # noqa: E402
from workbench.runner import _prepare_workdir, execute  # noqa: E402
from workbench.spec import Grader, load_suite  # noqa: E402
from workbench.stats import (  # noqa: E402
    bradley_terry, mcnemar, paired_table, required_pairs, sign_test,
    summarise_pairwise, wilson_interval,
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


def test_controls_and_errors() -> None:
    print("\nthe identical-pair control -- the cheapest test that blinding works")
    judge = _ScriptedJudge(["TIE", "TIE"])
    good = identical_pair_control(judge, "which is better", "the same answer")
    check("a judge that ties two identical answers passes the control", good["passed"])

    judge = _ScriptedJudge(["FIRST", "FIRST"])
    leaky = identical_pair_control(judge, "which is better", "the same answer")
    check("a judge that picks a winner between IDENTICAL answers FAILS the control",
          not leaky["passed"], str(leaky["verdicts"]))
    check("the control failure says the run cannot be trusted",
          "Do not trust" in leaky["detail"], leaky["detail"])

    print("\nunreadable verdicts must not become silent ties")

    class _Garbage(EchoBackend):
        def complete(self, request):
            return Completion(text="I would say the vibes are good",
                              structured=None, cost_usd=0.0)

    broken = judge_pair(_Garbage(), "c", Candidate("a", "x"), Candidate("b", "y"),
                        "c1", tokens=[])
    check("an unparseable judge verdict is recorded as ERROR, not TIE",
          broken.winner == "ERROR", broken.winner)
    check("errors are excluded from the position-bias rate",
          position_bias_rate([broken]) == 0.0)

    print("\nself-judging is flagged, not silently permitted")
    check("same family is detected",
          same_family("claude-haiku-4-5-20251001", "claude-haiku-4-5"))
    check("different families are not flagged",
          not same_family("claude-haiku-4-5", "claude-opus-5"))

    print("\nlength confound stays visible")
    lengths = length_summary([Candidate("short", "ab"), Candidate("long", "abcd")])
    check("length per variant is reported", lengths == {"short": 2, "long": 4})


def test_paired_outcomes() -> None:
    print("\npaired outcome comparison -- McNemar over shared cases")
    table = mcnemar(both_pass=3, a_only=5, b_only=0, both_fail=1)
    check("only the discordant cells count", table["discordant"] == 5)
    check("5 to 0 discordant is still not significant at n=5",
          not table["significant_at_0.05"], str(table["p_value_exact"]))
    check("9 to 0 discordant IS significant",
          mcnemar(0, 9, 0, 0)["significant_at_0.05"])

    identical = mcnemar(4, 0, 0, 2)
    check("no discordant pairs means the suite cannot separate the variants",
          "cannot separate" in identical["note"], identical["note"])

    paired = paired_table({"c1": True, "c2": True, "c3": False},
                          {"c1": True, "c2": False, "c3": False})
    check("the paired table is built from shared case ids", paired["cases"] == 3)
    check("it finds the one discordant case", paired["a_only"] == 1 and paired["b_only"] == 0)


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

    print("\n  an unreadable verdict must not be laundered into a tie")
    with_error = summarise_pairwise(["a", "a", "TIE", "ERROR", "b"], "a", "b")
    check("errors are counted separately", with_error["errors"] == 1)
    check("errors are excluded from the decided count", with_error["decided"] == 3)
    check("errors are excluded from the ties-as-half denominator",
          abs(with_error["win_rate_a_ties_as_half"] - 2.5 / 4) < 1e-9,
          str(with_error["win_rate_a_ties_as_half"]))
    check("an error is not counted as a tie", with_error["ties"] == 1)

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


def test_agent_mode_plumbing() -> None:
    """Agent mode grades a directory, so the directory plumbing needs proving.

    The echo backend cannot write files, so what is tested here is everything
    around the model call: that a fixture is copied into a fresh scratch
    directory, that setup commands run inside it, and that the filesystem
    graders read that directory rather than the process's cwd.
    """
    print("\nagent mode -- the artifact is a directory, not a string")

    fixture = Path(tempfile.mkdtemp(prefix="wb-fixture-")) / "seed"
    fixture.mkdir()
    (fixture / "given.txt").write_text("seeded content", encoding="utf-8")

    suite_dir = Path(tempfile.mkdtemp(prefix="wb-agentsuite-"))
    (suite_dir / "seed").mkdir()
    (suite_dir / "seed" / "given.txt").write_text("seeded content", encoding="utf-8")
    suite_path = suite_dir / "suite.yaml"
    suite_path.write_text("""
name: agentmode
variants:
  - id: v
    mode: agent
    fixture: seed
    setup: ["mkdir -p made && echo produced > made/output.txt"]
cases:
  - id: c
    prompt: 'do the thing'
    graders: [{type: contains, value: x}]
""", encoding="utf-8")
    suite = load_suite(suite_path)
    workdir = _prepare_workdir(suite, suite.cases[0], suite.variants[0])

    check("the fixture is copied into the scratch directory",
          (Path(workdir) / "given.txt").is_file())
    check("the scratch directory is not the fixture itself",
          Path(workdir).resolve() != (suite_dir / "seed").resolve())
    check("setup commands run inside it",
          (Path(workdir) / "made" / "output.txt").is_file())

    ctx = ctx_for("irrelevant output")
    ctx.workdir = workdir
    found = run_grader(Grader("file_exists", {"path": "made/*.txt"}), ctx)
    check("file_exists sees what the run produced", found.passed, found.detail)
    missing = run_grader(Grader("file_exists", {"path": "absent/*.txt"}), ctx)
    check("file_exists FAILS on a file that was not produced", not missing.passed)
    contains = run_grader(
        Grader("file_contains", {"path": "made/*.txt", "value": "produced"}), ctx)
    check("file_contains reads the produced file", contains.passed, contains.detail)
    absent = run_grader(
        Grader("file_contains", {"path": "made/*.txt", "value": "nope"}), ctx)
    check("file_contains FAILS when the text is not there", not absent.passed)

    print("\n  filesystem graders must refuse to pass in text mode")
    text_ctx = ctx_for("some text")
    no_dir = run_grader(Grader("file_exists", {"path": "*.txt"}), text_ctx)
    check("file_exists FAILS rather than passing without a working directory",
          not no_dir.passed and "agent mode" in no_dir.detail, no_dir.detail)


def test_thinking_controls() -> None:
    """Thinking control rides on flags absent from `claude --help`.

    They were found by probing the parser, so a test pinning the exact argv is
    the only thing standing between a silent CLI change and a run that reports
    a thinking budget it never applied.
    """
    print("\nthinking controls -- undocumented flags, so pin the argv")
    from workbench.backend import ClaudeCLIBackend

    backend = ClaudeCLIBackend()
    argv = backend._argv(Request(
        prompt="p", model="m", thinking="adaptive", max_thinking_tokens=2048,
    ))
    check("--thinking is passed", "--thinking" in argv and argv[argv.index("--thinking") + 1] == "adaptive")
    check("--max-thinking-tokens is passed",
          "--max-thinking-tokens" in argv
          and argv[argv.index("--max-thinking-tokens") + 1] == "2048")

    plain = backend._argv(Request(prompt="p"))
    check("neither appears when unset",
          "--thinking" not in plain and "--max-thinking-tokens" not in plain)

    check("max output tokens goes through the environment, not a flag",
          backend._env(Request(prompt="p", max_output_tokens=8000))
          .get("CLAUDE_CODE_MAX_OUTPUT_TOKENS") == "8000")
    check("no output-token flag is invented",
          "--max-tokens" not in backend._argv(Request(prompt="p", max_output_tokens=8000)))

    print("\n  thinking settings must change the cache key, or a sweep reuses one answer")
    base = Request(prompt="p", model="m")
    check("thinking mode changes the cache key",
          base.cache_key() != Request(prompt="p", model="m", thinking="adaptive").cache_key())
    check("thinking budget changes the cache key",
          base.cache_key() != Request(prompt="p", model="m", max_thinking_tokens=99).cache_key())
    check("output-token cap changes the cache key",
          base.cache_key() != Request(prompt="p", model="m", max_output_tokens=99).cache_key())


def test_multi_turn() -> None:
    print("\nmulti-turn -- a conversation, not a prompt")
    from workbench.backend import ClaudeCLIBackend

    backend = ClaudeCLIBackend()
    req = Request(turns=("first", "second"))
    argv = backend._argv(req)
    check("multi-turn uses the streaming transport both ways",
          "--input-format" in argv and "--output-format" in argv
          and argv[argv.index("--output-format") + 1] == "stream-json")
    check("--verbose is present, which the CLI requires for it",
          "--verbose" in argv)
    check("the prompt is not passed positionally", "first" not in argv)

    stdin = backend._stdin_for(req)
    lines = [json.loads(l) for l in stdin.strip().splitlines()]
    check("one NDJSON user event per turn", len(lines) == 2)
    check("each carries the turn text",
          lines[0]["message"]["content"][0]["text"] == "first"
          and lines[1]["message"]["content"][0]["text"] == "second")
    check("single-prompt requests send no stdin",
          backend._stdin_for(Request(prompt="p")) is None)

    print("\n  the last result event wins -- earlier ones are intermediate turns")
    stream = "\n".join([
        json.dumps({"type": "system"}),
        json.dumps({"type": "result", "result": "ACK", "usage": {}}),
        json.dumps({"type": "assistant"}),
        json.dumps({"type": "result", "result": "UNIT-42", "usage": {}}),
    ])
    final = backend._last_result(stream)
    check("the final result event is taken", final["result"] == "UNIT-42")
    check("a stream with no result event yields None",
          backend._last_result('{"type": "system"}') is None)
    check("unparseable lines are skipped, not fatal",
          backend._last_result('garbage\n' + json.dumps(
              {"type": "result", "result": "ok"}))["result"] == "ok")

    print("\n  turns change the cache key, and are graded end to end")
    check("turns change the cache key",
          Request(turns=("a",)).cache_key() != Request(turns=("a", "b")).cache_key())

    path = write_suite("""
name: mt
vars: {who: UNIT-42}
variants: [{id: v}]
cases:
  - id: convo
    turns:
      - 'My designation is {{who}}.'
      - 'What is it? [[echo: {{who}}]]'
    graders: [{type: contains, value: UNIT-42}]
""")
    result = execute(load_suite(path), EchoBackend(), report=lambda m: None)
    run = result.runs[0]
    check("a multi-turn case runs and grades", run.passed, run.output)
    check("variables render inside every turn", "{{who}}" not in run.prompt)
    check("the transcript records the whole conversation",
          "My designation" in run.prompt and "What is it" in run.prompt)

    rejects("a case setting both prompt and turns is refused",
            lambda: load_suite(write_suite(
                "name: t\nvariants: [{id: a}]\n"
                "cases: [{id: c, prompt: x, turns: [y]}]")), SpecError)
    rejects("a case with neither is refused",
            lambda: load_suite(write_suite(
                "name: t\nvariants: [{id: a}]\ncases: [{id: c}]")), SpecError)


def test_cache_is_per_backend() -> None:
    """An echo fixture must never be served to a live run.

    The request hash covers the prompt and the configuration but says nothing
    about who answered it. With one flat cache directory, an offline run using
    EchoBackend poisoned 36 entries that a live run then served as real model
    output, inside a measurement that cost $3 -- and the only reason it was
    caught is that one answer began with "echo(".
    """
    print("\ncache isolation -- whose answer is this?")
    from workbench.backend import CachingBackend, ClaudeCLIBackend

    cache = Path(tempfile.mkdtemp(prefix="wb-cache-"))
    echo = CachingBackend(EchoBackend(), cache)
    request = Request(prompt="the same prompt", model="claude-haiku-4-5")

    first = echo.complete(request)
    check("the echo backend answers and caches", first.text and echo.misses == 1)
    check("a second identical call hits its own cache",
          echo.complete(request).text == first.text and echo.hits == 1)

    # A different backend, same cache root, same request.
    live = CachingBackend(ClaudeCLIBackend(), cache)
    check("each backend gets its own cache directory",
          Path(echo.cache_dir) != Path(live.cache_dir),
          f"{echo.cache_dir} vs {live.cache_dir}")
    check("the live backend sees no hit from the echo run", live.hits == 0)

    # And if an entry from another backend somehow lands in the directory, it
    # must be refused rather than reported as this backend's answer.
    class _Pretend(EchoBackend):
        """Stands in for a live backend: a distinct name, no network."""
        name = "pretend-live"

        def complete(self, request):
            return Completion(text="a real answer", backend=self.name, cost_usd=0.0)

    pretend = CachingBackend(_Pretend(), cache)
    stray = Path(pretend.cache_dir) / f"{request.cache_key()}.json"
    stray.parent.mkdir(parents=True, exist_ok=True)
    stray.write_text(json.dumps({"text": "echo(deadbeef): not mine",
                                 "backend": "echo"}), encoding="utf-8")
    result = pretend.complete(request)
    check("a cross-backend entry is refused, not served",
          result.text == "a real answer", result.text[:60])
    check("the refusal counts as a miss, not a hit", pretend.hits == 0)
    check("and the stray entry is replaced, not left to mislead the next run",
          json.loads(stray.read_text()).get("backend") == "pretend-live")


def test_length_stratification() -> None:
    """The control that separates a real preference from a length effect."""
    print("\nlength stratification -- is the judge reading content or word count?")
    from workbench.report import length_stratified
    from workbench.runner import CaseRun, RunResult
    from workbench.blind import PairJudgement

    result = RunResult(suite="s", run_id="r", backend="echo", started_at="now")
    # Two cases where A is longer, two where B is. A wins all four.
    plan = [("c1", 500, 100), ("c2", 500, 100), ("c3", 100, 500), ("c4", 100, 500)]
    for case, a_len, b_len in plan:
        result.runs.append(CaseRun(case_id=case, variant_id="A", repeat=0,
                                   prompt="p", output="x" * a_len))
        result.runs.append(CaseRun(case_id=case, variant_id="B", repeat=0,
                                   prompt="p", output="x" * b_len))
        result.judgements.append(PairJudgement(case_id=case, left="A", right="B",
                                               winner="A", agreed=True))
    rows = {r["stratum"]: r for r in length_stratified(result)}
    check("both strata are reported", len(rows) == 2, str(list(rows)))
    check("the stratum where A was longer holds 2 pairs",
          rows["A was longer"]["pairs"] == 2)
    check("the stratum where B was longer holds 2 pairs",
          rows["B was longer or equal"]["pairs"] == 2)
    check("A's wins are counted in both strata",
          rows["A was longer"]["wins_a"] == 2
          and rows["B was longer or equal"]["wins_a"] == 2)

    print("\n  a pure length effect must show up as a one-sided stratum")
    biased = RunResult(suite="s", run_id="r", backend="echo", started_at="now")
    for case, a_len, b_len in plan:
        biased.runs.append(CaseRun(case_id=case, variant_id="A", repeat=0,
                                   prompt="p", output="x" * a_len))
        biased.runs.append(CaseRun(case_id=case, variant_id="B", repeat=0,
                                   prompt="p", output="x" * b_len))
        # The judge always picks whichever answer is longer.
        biased.judgements.append(PairJudgement(
            case_id=case, left="A", right="B",
            winner="A" if a_len > b_len else "B", agreed=True))
    rows = {r["stratum"]: r for r in length_stratified(biased)}
    check("a length-following judge wins A only where A was longer",
          rows["A was longer"]["wins_a"] == 2 and rows["A was longer"]["wins_b"] == 0)
    check("and loses A entirely where B was longer",
          rows["B was longer or equal"]["wins_a"] == 0
          and rows["B was longer or equal"]["wins_b"] == 2)
    check("so the two strata disagree, which is the signal to look for",
          rows["A was longer"]["wins_a"] > rows["B was longer or equal"]["wins_a"])


def test_errored_runs_are_not_graded() -> None:
    """A transport failure is not a wrong answer.

    A TLS error on one arm of a held-out comparison was graded 1.33/5 by a
    judge and surfaced as the single discordant case -- that is, as evidence
    that the other arm was better. The backend never answered.
    """
    print("\nerrored runs -- excluded, not scored")
    from workbench.runner import CaseRun
    from workbench.report import variant_rollup, markdown
    from workbench.runner import RunResult

    broken = Completion(text="API Error: Unable to connect to API", error="tls failure")
    run = CaseRun(case_id="c", variant_id="v", repeat=0, prompt="p",
                  output=broken.text, completion=broken)
    check("a completion the backend rejected is marked errored", run.errored)
    check("and it does not count as a pass", not run.passed)

    empty = CaseRun(case_id="c", variant_id="v", repeat=0, prompt="p", output="",
                    completion=Completion(text="   "))
    check("an empty response is errored too", empty.errored)

    good = CaseRun(case_id="c", variant_id="v", repeat=0, prompt="p", output="fine",
                   completion=Completion(text="fine"),
                   verdicts=[Verdict(grader="g", kind=DETERMINISTIC, passed=True, score=1.0)])
    check("a real answer is not errored", not good.errored and good.passed)

    print("\n  an errored run must not make the other variant look better")
    result = RunResult(suite="s", run_id="r", backend="b", started_at="now")
    result.runs = [
        CaseRun(case_id="c1", variant_id="A", repeat=0, prompt="p", output="ok",
                completion=Completion(text="ok"),
                verdicts=[Verdict(grader="g", kind=DETERMINISTIC, passed=True, score=1.0)]),
        CaseRun(case_id="c1", variant_id="B", repeat=0, prompt="p",
                output="API Error", completion=broken),
    ]
    rows = {r["variant"]: r for r in variant_rollup(result)}
    check("the errored variant reports zero scored runs", rows["B"]["runs"] == 0)
    check("and its error is counted separately", rows["B"]["errored"] == 1)
    check("the healthy variant is unaffected", rows["A"]["runs"] == 1 and rows["A"]["passed"] == 1)

    rendered = markdown(result)
    check("the report says errored runs were excluded",
          "excluded" in rendered.lower())
    check("the paired table does not score the errored case",
          "Discordant cases: **0**" in rendered or "cannot separate" in rendered,
          "paired table should find nothing to compare")


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
    test_controls_and_errors()
    test_paired_outcomes()
    test_statistics()
    test_end_to_end()
    test_agent_mode_plumbing()
    test_thinking_controls()
    test_multi_turn()
    test_cache_is_per_backend()
    test_length_stratification()
    test_errored_runs_are_not_graded()
    test_registry_kinds()

    print()
    if FAILURES:
        print(f"{len(FAILURES)} case(s) failed: {', '.join(FAILURES)}")
        return 1
    print("all cases passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
