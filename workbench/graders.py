"""Graders, ordered by how much they cost you in trust.

The ordering principle: **ask a model only what nothing cheaper can settle.**
A regex that checks for a citation tag is free, instant, and returns the same
answer every time. A judge asked "does this look well sourced?" costs money,
takes seconds, and returns a different answer on Tuesday. Both are legitimate;
using the second where the first would do is not.

So every grader declares its ``kind``:

``deterministic``
    Same input, same verdict, forever. Text matching, schema checks, numbers.
``environmental``
    Depends on the machine -- a shell command, a file on disk, a cost ceiling.
    Reproducible given the same environment, which is a weaker promise.
``model``
    A model decided. Reported separately so a reader can see how much of a
    result rests on a judgement call.

The report prints the split. A suite whose score is 90% model-graded is not
the same evidence as one that is 90% deterministic, and the difference should
be visible without reading the suite file.
"""

from __future__ import annotations

import json
import re
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from .backend import Backend, Completion, Request
from .errors import GraderError
from .spec import Grader

DETERMINISTIC = "deterministic"
ENVIRONMENTAL = "environmental"
MODEL = "model"


@dataclass
class Verdict:
    """One grader's answer about one output."""

    grader: str
    kind: str
    passed: bool
    score: float          # 0.0 - 1.0; binary graders report 0.0 or 1.0
    detail: str = ""
    weight: float = 1.0
    advisory: bool = False
    cost_usd: float = 0.0
    #: For judges: the individual votes, so a 2-1 is distinguishable from 3-0.
    votes: list[Any] = field(default_factory=list)
    #: The grader could not produce a judgement at all -- e.g. every judge call
    #: returned unreadable output. Distinct from `passed=False`, which is a
    #: verdict AGAINST the candidate. A run carrying one of these is excluded
    #: from the statistics rather than counted as a failure.
    errored: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "grader": self.grader, "kind": self.kind, "passed": self.passed,
            "score": round(self.score, 4), "detail": self.detail[:2000],
            "weight": self.weight, "advisory": self.advisory,
            "cost_usd": round(self.cost_usd, 6),
            "votes": self.votes, "errored": self.errored,
        }


@dataclass
class GradingContext:
    """Everything a grader is allowed to look at."""

    completion: Completion
    case_id: str
    variant_id: str
    vars: dict[str, Any] = field(default_factory=dict)
    workdir: str = ""
    #: The suite file's own directory. Commands anchor to this rather than to
    #: the process's cwd, so a suite stays runnable from anywhere.
    suite_dir: str = ""
    #: Only supplied to model graders, and only when a judge is configured.
    judge_backend: Backend | None = None
    judge_model: str | None = None
    judge_votes: int = 1

    @property
    def output(self) -> str:
        return self.completion.text


GraderFn = Callable[[Grader, GradingContext], Verdict]
REGISTRY: dict[str, tuple[str, GraderFn]] = {}


def grader(name: str, kind: str) -> Callable[[GraderFn], GraderFn]:
    def decorate(fn: GraderFn) -> GraderFn:
        REGISTRY[name] = (kind, fn)
        return fn
    return decorate


def _need(g: Grader, key: str) -> Any:
    if key not in g.config:
        raise GraderError(f"grader {g.type!r} requires `{key}`")
    return g.config[key]


def _need_list(g: Grader, key: str) -> list[Any]:
    """Require a list, and refuse a bare string rather than iterating it.

    `values: hello` is valid YAML and means the string "hello", so iterating it
    yields five single characters -- and `contains_any` then reported "matched
    5/5" against any English sentence containing h, e, l and o. A grader that
    passes almost everything is worse than one that errors, because it looks
    like evidence. This refuses the suite instead.
    """
    value = _need(g, key)
    if isinstance(value, (str, bytes)) or not isinstance(value, (list, tuple)):
        raise GraderError(
            f"grader {g.type!r} requires `{key}` to be a list, got "
            f"{type(value).__name__} {value!r}. A bare string would be iterated "
            f"character by character; write `{key}: [{value!r}]` if you meant one item.")
    return list(value)


def _binary(g: Grader, kind: str, passed: bool, detail: str) -> Verdict:
    return Verdict(
        grader=g.label, kind=kind, passed=passed, score=1.0 if passed else 0.0,
        detail=detail, weight=g.weight, advisory=g.advisory,
    )


# --------------------------------------------------------------------------
# Text matching
# --------------------------------------------------------------------------

@grader("equals", DETERMINISTIC)
def g_equals(g: Grader, ctx: GradingContext) -> Verdict:
    expected = str(_need(g, "value"))
    actual = ctx.output
    if g.config.get("strip", True):
        expected, actual = expected.strip(), actual.strip()
    if g.config.get("ignore_case", False):
        expected, actual = expected.lower(), actual.lower()
    ok = actual == expected
    return _binary(g, DETERMINISTIC, ok,
                   "exact match" if ok else f"expected {expected!r}, got {actual[:200]!r}")


@grader("contains", DETERMINISTIC)
def g_contains(g: Grader, ctx: GradingContext) -> Verdict:
    needle = str(_need(g, "value"))
    hay = ctx.output
    if g.config.get("ignore_case", True):
        needle, hay = needle.lower(), hay.lower()
    ok = needle in hay
    return _binary(g, DETERMINISTIC, ok,
                   f"found {needle!r}" if ok else f"{needle!r} not present")


@grader("not_contains", DETERMINISTIC)
def g_not_contains(g: Grader, ctx: GradingContext) -> Verdict:
    needle = str(_need(g, "value"))
    hay = ctx.output
    if g.config.get("ignore_case", True):
        needle, hay = needle.lower(), hay.lower()
    ok = needle not in hay
    return _binary(g, DETERMINISTIC, ok,
                   f"absent as required" if ok else f"forbidden text {needle!r} present")


@grader("contains_any", DETERMINISTIC)
def g_contains_any(g: Grader, ctx: GradingContext) -> Verdict:
    values = _need_list(g, "values")
    hay = ctx.output.lower() if g.config.get("ignore_case", True) else ctx.output
    hits = [v for v in values
            if (str(v).lower() if g.config.get("ignore_case", True) else str(v)) in hay]
    minimum = int(g.config.get("min", 1))
    ok = len(hits) >= minimum
    return _binary(g, DETERMINISTIC, ok, f"matched {len(hits)}/{len(values)}: {hits[:8]}")


@grader("contains_all", DETERMINISTIC)
def g_contains_all(g: Grader, ctx: GradingContext) -> Verdict:
    values = [str(v) for v in _need_list(g, "values")]
    ic = g.config.get("ignore_case", True)
    hay = ctx.output.lower() if ic else ctx.output
    missing = [v for v in values if (v.lower() if ic else v) not in hay]
    return _binary(g, DETERMINISTIC, not missing,
                   "all present" if not missing else f"missing: {missing}")


@grader("regex", DETERMINISTIC)
def g_regex(g: Grader, ctx: GradingContext) -> Verdict:
    pattern = str(_need(g, "pattern"))
    flags = 0
    for flag in str(g.config.get("flags", "")).lower():
        flags |= {"i": re.I, "m": re.M, "s": re.S, "x": re.X}.get(flag, 0)
    try:
        rx = re.compile(pattern, flags)
    except re.error as exc:
        raise GraderError(f"regex grader: bad pattern {pattern!r}: {exc}") from exc
    matches = rx.findall(ctx.output)
    expect = str(g.config.get("match", "present"))
    if expect in ("present", "contains"):
        ok = bool(matches)
    elif expect in ("absent", "not_contains"):
        ok = not matches
    elif expect.startswith("count:"):
        ok = len(matches) == int(expect.split(":", 1)[1])
    elif expect.startswith("min:"):
        ok = len(matches) >= int(expect.split(":", 1)[1])
    else:
        raise GraderError(
            f"regex grader: `match` must be present|absent|count:N|min:N, got {expect!r}"
        )
    return _binary(g, DETERMINISTIC, ok,
                   f"{len(matches)} match(es) for /{pattern}/, wanted {expect}")


# --------------------------------------------------------------------------
# Structure
# --------------------------------------------------------------------------

def _extract_json(text: str) -> Any:
    """Parse JSON, tolerating a fenced code block around it."""
    candidate = text.strip()
    fence = re.search(r"```(?:json)?\s*(.+?)```", candidate, re.S)
    if fence:
        candidate = fence.group(1).strip()
    return json.loads(candidate)


@grader("json_valid", DETERMINISTIC)
def g_json_valid(g: Grader, ctx: GradingContext) -> Verdict:
    payload = ctx.completion.structured
    if payload is not None:
        return _binary(g, DETERMINISTIC, True, "backend returned structured output")
    try:
        _extract_json(ctx.output)
    except (json.JSONDecodeError, ValueError) as exc:
        return _binary(g, DETERMINISTIC, False, f"not JSON: {exc}")
    return _binary(g, DETERMINISTIC, True, "parsed as JSON")


def validate_grader(g: Grader) -> None:
    """Raise GraderError if this grader is misconfigured, without calling a model.

    Config errors in a grader surface at the first case, after a run has
    started and possibly after money has been spent. `workbench new` shipped a
    template using `criterion:` where the judge grader wants `criteria:`: it
    loaded cleanly, then died on the first case. load_suite cannot catch that,
    because it validates suite structure and leaves grader config to the
    grader.

    Deterministic and environmental graders are exercised against a dummy
    output -- a grader that RUNS and returns False has validated; only a
    GraderError means the config is wrong. Model graders cannot be exercised
    without a judge, so their required keys are checked directly.
    """
    if g.type not in REGISTRY:
        raise GraderError(f"unknown grader type {g.type!r}; "
                          f"known: {', '.join(sorted(REGISTRY))}")
    kind, fn = REGISTRY[g.type]          # (kind, fn) -- unpacking this
    if not callable(fn):                 # backwards silently disabled the
        raise GraderError(               # whole check, so assert the shape
            f"registry entry for {g.type!r} is malformed: {fn!r} is not callable")
    if kind == MODEL:
        if not (g.config.get("criteria") or g.config.get("rubric")):
            raise GraderError(
                f"grader {g.type!r} requires `criteria` (or `rubric`); "
                f"got keys {sorted(g.config) or '[]'}")
        return
    ctx = GradingContext(
        completion=Completion(text="a probe output for config validation", model="probe"),
        case_id="_validate", variant_id="_validate")
    try:
        fn(g, ctx)
    except GraderError:
        raise
    except (TypeError, AttributeError):
        # These mean the grader was CALLED wrongly, not that the probe text
        # displeased it -- exactly what a backwards registry unpack produces.
        # Swallowing them is how this function silently accepted a judge
        # grader with no criteria while appearing to work.
        raise
    except Exception:                                          # noqa: BLE001
        # It ran and blew up on the probe text rather than on its config --
        # a `command` grader with no such binary, say. Not a config error.
        return


def validate_schema(value: Any, schema: dict[str, Any], path: str = "$") -> list[str]:
    """A deliberately small JSON Schema subset.

    Supported: ``type``, ``properties``, ``required``, ``additionalProperties``,
    ``items``, ``enum``, ``minimum``, ``maximum``, ``minLength``, ``maxLength``,
    ``minItems``, ``maxItems``, ``pattern``.

    Anything else in the schema is ignored rather than silently treated as
    satisfied -- :func:`unsupported_schema_keys` reports it so a suite author
    is told their constraint is not being enforced.
    """
    errors: list[str] = []
    expected = schema.get("type")
    if expected:
        types = expected if isinstance(expected, list) else [expected]
        matched = any(
            (t == "object" and isinstance(value, dict))
            or (t == "array" and isinstance(value, list))
            or (t == "string" and isinstance(value, str))
            or (t == "boolean" and isinstance(value, bool))
            or (t == "integer" and isinstance(value, int) and not isinstance(value, bool))
            or (t == "number" and isinstance(value, (int, float)) and not isinstance(value, bool))
            or (t == "null" and value is None)
            for t in types
        )
        if not matched:
            errors.append(f"{path}: expected type {expected}, got {type(value).__name__}")
            return errors
    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{path}: {value!r} not in enum {schema['enum']}")
    if isinstance(value, dict):
        for key in schema.get("required", []):
            if key not in value:
                errors.append(f"{path}: missing required property {key!r}")
        props = schema.get("properties", {})
        for key, sub in props.items():
            if key in value:
                errors.extend(validate_schema(value[key], sub, f"{path}.{key}"))
        if schema.get("additionalProperties") is False:
            extra = sorted(set(value) - set(props))
            if extra:
                errors.append(f"{path}: unexpected propert(ies) {extra}")
    if isinstance(value, list):
        if "items" in schema:
            for i, item in enumerate(value):
                errors.extend(validate_schema(item, schema["items"], f"{path}[{i}]"))
        if "minItems" in schema and len(value) < schema["minItems"]:
            errors.append(f"{path}: {len(value)} items < minItems {schema['minItems']}")
        if "maxItems" in schema and len(value) > schema["maxItems"]:
            errors.append(f"{path}: {len(value)} items > maxItems {schema['maxItems']}")
    if isinstance(value, str):
        if "minLength" in schema and len(value) < schema["minLength"]:
            errors.append(f"{path}: length {len(value)} < minLength {schema['minLength']}")
        if "maxLength" in schema and len(value) > schema["maxLength"]:
            errors.append(f"{path}: length {len(value)} > maxLength {schema['maxLength']}")
        if "pattern" in schema and not re.search(schema["pattern"], value):
            errors.append(f"{path}: does not match /{schema['pattern']}/")
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if "minimum" in schema and value < schema["minimum"]:
            errors.append(f"{path}: {value} < minimum {schema['minimum']}")
        if "maximum" in schema and value > schema["maximum"]:
            errors.append(f"{path}: {value} > maximum {schema['maximum']}")
    return errors


_SUPPORTED_SCHEMA_KEYS = {
    "type", "properties", "required", "additionalProperties", "items", "enum",
    "minimum", "maximum", "minLength", "maxLength", "minItems", "maxItems",
    "pattern", "description", "title", "$schema",
}


def unsupported_schema_keys(schema: Any, path: str = "$") -> list[str]:
    """Report schema keywords this validator does not enforce."""
    found: list[str] = []
    if isinstance(schema, dict):
        for key, sub in schema.items():
            if key not in _SUPPORTED_SCHEMA_KEYS:
                found.append(f"{path}.{key}")
            if key in ("properties",) and isinstance(sub, dict):
                for name, s in sub.items():
                    found.extend(unsupported_schema_keys(s, f"{path}.properties.{name}"))
            elif key == "items":
                found.extend(unsupported_schema_keys(sub, f"{path}.items"))
    return found


@grader("json_schema", DETERMINISTIC)
def g_json_schema(g: Grader, ctx: GradingContext) -> Verdict:
    schema = _need(g, "schema")
    payload = ctx.completion.structured
    if payload is None:
        try:
            payload = _extract_json(ctx.output)
        except (json.JSONDecodeError, ValueError) as exc:
            return _binary(g, DETERMINISTIC, False, f"output is not JSON: {exc}")
    errors = validate_schema(payload, schema)
    unsupported = unsupported_schema_keys(schema)
    note = ""
    if unsupported:
        note = f" (not enforced by this validator: {', '.join(unsupported[:5])})"
    return _binary(g, DETERMINISTIC, not errors,
                   ("conforms" if not errors else "; ".join(errors[:6])) + note)


@grader("json_path", DETERMINISTIC)
def g_json_path(g: Grader, ctx: GradingContext) -> Verdict:
    dotted = str(_need(g, "path"))
    payload = ctx.completion.structured
    if payload is None:
        try:
            payload = _extract_json(ctx.output)
        except (json.JSONDecodeError, ValueError) as exc:
            return _binary(g, DETERMINISTIC, False, f"output is not JSON: {exc}")
    cursor: Any = payload
    for part in [p for p in dotted.split(".") if p]:
        if isinstance(cursor, list) and part.isdigit():
            index = int(part)
            if index >= len(cursor):
                return _binary(g, DETERMINISTIC, False, f"{dotted}: index {index} out of range")
            cursor = cursor[index]
        elif isinstance(cursor, dict) and part in cursor:
            cursor = cursor[part]
        else:
            return _binary(g, DETERMINISTIC, False, f"{dotted}: no such key {part!r}")
    if "equals" in g.config:
        ok = cursor == g.config["equals"]
        return _binary(g, DETERMINISTIC, ok, f"{dotted} = {cursor!r} (wanted {g.config['equals']!r})")
    return _binary(g, DETERMINISTIC, True, f"{dotted} = {cursor!r}")


# --------------------------------------------------------------------------
# Shape and budget
# --------------------------------------------------------------------------

@grader("word_count", DETERMINISTIC)
def g_word_count(g: Grader, ctx: GradingContext) -> Verdict:
    count = len(ctx.output.split())
    lo, hi = g.config.get("min"), g.config.get("max")
    ok = (lo is None or count >= int(lo)) and (hi is None or count <= int(hi))
    return _binary(g, DETERMINISTIC, ok, f"{count} words (min={lo}, max={hi})")


@grader("no_error", DETERMINISTIC)
def g_no_error(g: Grader, ctx: GradingContext) -> Verdict:
    ok = ctx.completion.ok and bool(ctx.output.strip())
    return _binary(g, DETERMINISTIC, ok,
                   ctx.completion.error or ("non-empty response" if ok else "empty response"))


@grader("cost_under", ENVIRONMENTAL)
def g_cost_under(g: Grader, ctx: GradingContext) -> Verdict:
    ceiling = float(_need(g, "usd"))
    actual = ctx.completion.cost_usd
    if actual is None:
        return _binary(g, ENVIRONMENTAL, True, "backend reports no cost; not enforced")
    return _binary(g, ENVIRONMENTAL, actual <= ceiling, f"${actual:.6f} vs ceiling ${ceiling}")


@grader("latency_under", ENVIRONMENTAL)
def g_latency_under(g: Grader, ctx: GradingContext) -> Verdict:
    ceiling = float(_need(g, "ms"))
    return _binary(g, ENVIRONMENTAL, ctx.completion.duration_ms <= ceiling,
                   f"{ctx.completion.duration_ms}ms vs ceiling {ceiling}ms")


@grader("tokens_under", ENVIRONMENTAL)
def g_tokens_under(g: Grader, ctx: GradingContext) -> Verdict:
    ceiling = int(_need(g, "output_tokens"))
    return _binary(g, ENVIRONMENTAL, ctx.completion.output_tokens <= ceiling,
                   f"{ctx.completion.output_tokens} output tokens vs ceiling {ceiling}")


# --------------------------------------------------------------------------
# Outcome graders -- these look at what the run produced, not what it said
# --------------------------------------------------------------------------

@grader("command", ENVIRONMENTAL)
def g_command(g: Grader, ctx: GradingContext) -> Verdict:
    """Run a shell command over the output. Exit 0 passes.

    This is the outcome-based grader: it hands the artifact to a real checker
    -- a linter, a test runner, this repository's own provenance verifier --
    and takes that program's word for it. Placeholders ``{output_file}``,
    ``{workdir}`` and ``{suite_dir}`` are substituted into the command.

    **A suite file is executable code.** This runs with ``shell=True``, so a
    suite is exactly as trustworthy as whoever wrote it -- running one from an
    untrusted source is running their shell script. That is a deliberate
    tradeoff: sandboxing the grader would rule out the checkers that make
    outcome-based grading worth having. Review a suite before running it, the
    same way you would a Makefile or a CI config.
    """
    command = str(_need(g, "command"))
    expect_code = int(g.config.get("exit_code", 0))
    timeout = int(g.config.get("timeout_s", 120))
    with tempfile.TemporaryDirectory(prefix="wb-grade-") as tmp:
        output_file = Path(tmp) / "output.txt"
        output_file.write_text(ctx.output, encoding="utf-8")
        rendered = command.replace("{output_file}", str(output_file))
        rendered = rendered.replace("{workdir}", ctx.workdir or tmp)
        rendered = rendered.replace("{suite_dir}", ctx.suite_dir)
        try:
            proc = subprocess.run(
                rendered, shell=True, capture_output=True, text=True,
                timeout=timeout, cwd=ctx.workdir or tmp,
            )
        except subprocess.TimeoutExpired:
            return _binary(g, ENVIRONMENTAL, False, f"command timed out after {timeout}s")
        ok = proc.returncode == expect_code
        tail = (proc.stdout + proc.stderr).strip()[-600:]
        return _binary(g, ENVIRONMENTAL, ok,
                       f"exit {proc.returncode} (wanted {expect_code})"
                       + (f"\n{tail}" if tail else ""))


@grader("file_exists", ENVIRONMENTAL)
def g_file_exists(g: Grader, ctx: GradingContext) -> Verdict:
    """Agent-mode outcome: did the run actually create the file it claimed to?"""
    pattern = str(_need(g, "path"))
    if not ctx.workdir:
        return _binary(g, ENVIRONMENTAL, False,
                       "file_exists needs agent mode (no working directory)")
    matches = sorted(str(p.relative_to(ctx.workdir))
                     for p in Path(ctx.workdir).glob(pattern))
    expect = g.config.get("expect", "present")
    ok = bool(matches) if expect == "present" else not matches
    return _binary(g, ENVIRONMENTAL, ok, f"{len(matches)} match(es) for {pattern}: {matches[:6]}")


@grader("file_contains", ENVIRONMENTAL)
def g_file_contains(g: Grader, ctx: GradingContext) -> Verdict:
    pattern = str(_need(g, "path"))
    needle = str(_need(g, "value"))
    if not ctx.workdir:
        return _binary(g, ENVIRONMENTAL, False, "file_contains needs agent mode")
    for path in sorted(Path(ctx.workdir).glob(pattern)):
        try:
            if needle in path.read_text(encoding="utf-8", errors="replace"):
                return _binary(g, ENVIRONMENTAL, True, f"found in {path.name}")
        except OSError:
            continue
    return _binary(g, ENVIRONMENTAL, False, f"{needle!r} in no file matching {pattern}")


# --------------------------------------------------------------------------
# Model grader
# --------------------------------------------------------------------------

JUDGE_SCHEMA = {
    "type": "object",
    "properties": {
        "score": {"type": "integer", "minimum": 1, "maximum": 5},
        "passed": {"type": "boolean"},
        "reason": {"type": "string"},
    },
    "required": ["score", "passed", "reason"],
    "additionalProperties": False,
}

JUDGE_SYSTEM = (
    "You are a strict evaluator. You are shown a candidate answer and a "
    "criterion. Judge only whether the candidate satisfies the criterion. "
    "You do not know which system produced the candidate and must not "
    "speculate about it. Ignore length, confidence and style except where the "
    "criterion is about them. Return only the requested JSON object."
)


@grader("judge", MODEL)
def g_judge(g: Grader, ctx: GradingContext) -> Verdict:
    """Rubric grading by a model, run blind and optionally by majority vote.

    The judge is never told the variant id, the model name, or the system
    prompt under test. It gets the criterion and the candidate text, nothing
    else -- because a judge that knows which arm is the "new" one is not a
    judge, it is a rubber stamp.
    """
    criterion = str(_need(g, "criteria") if "criteria" in g.config else _need(g, "rubric"))
    if ctx.judge_backend is None:
        raise GraderError(
            "a `judge` grader was configured but no judge backend is available; "
            "run with --backend claude-cli, or drop the grader"
        )
    threshold = int(g.config.get("pass_score", 4))
    votes_wanted = int(g.config.get("votes", ctx.judge_votes))
    if votes_wanted % 2 == 0:
        votes_wanted += 1  # an even panel can tie; make ties impossible

    prompt = (
        f"CRITERION\n{criterion}\n\n"
        f"CANDIDATE ANSWER\n<<<CANDIDATE\n{ctx.output}\nCANDIDATE\n\n"
        f"Score 1-5 for how well the candidate satisfies the criterion "
        f"(5 = fully, 1 = not at all). Set `passed` true only if the score is "
        f"{threshold} or more."
    )
    votes: list[dict[str, Any]] = []
    cost = 0.0
    for i in range(votes_wanted):
        completion = ctx.judge_backend.complete(Request(
            prompt=prompt,
            system=JUDGE_SYSTEM,
            model=ctx.judge_model,
            json_schema=JUDGE_SCHEMA,
            tools="",
            repeat=i,
        ))
        cost += completion.cost_usd or 0.0
        payload = completion.structured
        if payload is None:
            try:
                payload = _extract_json(completion.text)
            except (json.JSONDecodeError, ValueError):
                # NOT a failing vote. A judge that returned unreadable output
                # has said nothing about the candidate, and scoring it 0 makes
                # a judge-side transport or format failure look like evidence
                # the answer was bad. blind.py refuses this coercion already --
                # an unparseable verdict there becomes "ERROR", never a tie --
                # and this path was making exactly the mistake that module was
                # written to avoid.
                payload = {"unreadable": True,
                           "reason": f"judge returned unparseable output: {completion.text[:200]}"}
        votes.append(payload)

    usable = [v for v in votes if not v.get("unreadable")]
    unreadable = len(votes) - len(usable)

    if not usable:
        # Every judge failed to answer. There is no verdict to report, so this
        # is surfaced as an error rather than as a failing grade.
        return Verdict(
            grader=g.label, kind=MODEL, passed=False, score=0.0,
            detail=f"no usable judgement: all {len(votes)} judge call(s) returned "
                   f"unreadable output. This is a judge failure, not a verdict "
                   f"about the candidate.",
            weight=g.weight, advisory=g.advisory, cost_usd=cost,
            votes=votes, errored=True,
        )

    passes = sum(1 for v in usable if v.get("passed"))
    scores = [int(v.get("score", 0)) for v in usable]
    majority = passes * 2 > len(usable)
    mean = sum(scores) / len(scores) if scores else 0.0
    note = (f" ({unreadable} of {len(votes)} judge call(s) returned unreadable "
            f"output and were excluded)" if unreadable else "")
    return Verdict(
        grader=g.label, kind=MODEL, passed=majority,
        score=max(0.0, min(1.0, (mean - 1) / 4)),
        detail=f"{passes}/{len(usable)} judges passed it; mean score {mean:.2f}/5.{note} "
               + (usable[0].get("reason", "") if usable else ""),
        weight=g.weight, advisory=g.advisory, cost_usd=cost,
        votes=votes,
    )


# --------------------------------------------------------------------------

def run_grader(g: Grader, ctx: GradingContext) -> Verdict:
    entry = REGISTRY.get(g.type)
    if entry is None:
        raise GraderError(
            f"unknown grader type {g.type!r}. Known: {', '.join(sorted(REGISTRY))}"
        )
    _kind, fn = entry
    try:
        return fn(g, ctx)
    except GraderError:
        raise
    except Exception as exc:  # a broken grader must not be scored as a pass
        return Verdict(
            grader=g.label, kind=_kind, passed=False, score=0.0,
            detail=f"grader raised {type(exc).__name__}: {exc}",
            weight=g.weight, advisory=g.advisory,
        )


def grade(graders: tuple[Grader, ...], ctx: GradingContext) -> list[Verdict]:
    return [run_grader(g, ctx) for g in graders]


def describe_registry() -> list[tuple[str, str]]:
    """``(name, kind)`` for every registered grader, for ``workbench graders``."""
    return sorted((name, kind) for name, (kind, _fn) in REGISTRY.items())
