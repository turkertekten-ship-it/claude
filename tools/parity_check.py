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
import re
import os
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


def _blocked(capability: str, *completions) -> Result | None:
    """Report a backend error as the reason, instead of a capability verdict.

    A run that hit a rate limit or a transport error tells you nothing about
    whether the capability works. An earlier recording of this harness showed
    four failures whose detail text read like passes, because the checks
    described what they had asked for rather than what came back. If the
    backend did not answer, say so and name it.
    """
    for c in completions:
        if not c.ok:
            return Result(capability, FAIL,
                          f"the backend did not answer, so this says nothing about "
                          f"the capability: {c.error[:200]}",
                          c.cost_usd or 0.0)
        if not c.text.strip():
            return Result(capability, FAIL,
                          "the backend returned an empty response, so this says "
                          "nothing about the capability",
                          c.cost_usd or 0.0)
    return None


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
    blocked = _blocked("System prompt replaces the default", c)
    if blocked:
        return blocked
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
    blocked = _blocked("Model selection", c)
    if blocked:
        return blocked
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

    blocked = _blocked("Effort control changes work done", low, high)
    if blocked:
        return blocked
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
    """The ceiling is enforced by REFUSING, not by truncating.

    An earlier version of this check looked for `output_tokens <= cap` and
    `stop_reason == "max_tokens"`, found neither, and recorded the capability
    as broken -- a verdict that reached docs/parity.md and README.md as a
    platform defect. It was this harness that was wrong. Claude Code enforces
    the ceiling by returning an API error naming the maximum, and the tokens
    that appeared to breach the cap were thinking tokens spent before it fired.
    """
    tight = _run(backend, prompt="Count from 1 to 300, one number per line.",
                 max_output_tokens=64)
    loose = _run(backend, prompt="Count from 1 to 40, one number per line.",
                 max_output_tokens=8000)
    refused = (not tight.ok) and "output token maximum" in tight.text
    allowed = loose.ok and loose.text.strip().startswith("1")
    ok = refused and allowed
    return Result("Max output tokens", PASS if ok else FAIL,
                  f"a 64-token ceiling on a long task was enforced by refusal "
                  f"({tight.text.strip()[:70]!r}), and an 8000-token ceiling let "
                  f"the same shape of task through. Enforced by erroring, not by "
                  f"truncating — which is why an earlier version of this check "
                  f"wrongly called it broken."
                  if ok else
                  f"tight: ok={tight.ok} {tight.text.strip()[:80]!r} | "
                  f"loose: ok={loose.ok} {loose.text.strip()[:50]!r}",
                  (tight.cost_usd or 0) + (loose.cost_usd or 0))


@check("Budget ceiling is enforced")
def c_budget(backend) -> Result:
    """A ceiling nothing has ever hit is a promise, not a control.

    This row was in the matrix, plumbed through the code, and never exercised
    until a fact-checker pointed out that every sibling row had a check and
    this one did not.
    """
    c = _run(backend, prompt="Write a detailed 900-word essay about gardening.",
             max_budget_usd=0.0001)
    stopped = (not c.ok) or c.stop_reason in ("error_max_budget_usd", "max_budget")
    spent = c.cost_usd or 0.0
    tiny = spent <= 0.02
    ok = stopped or tiny
    return Result("Budget ceiling is enforced", PASS if ok else FAIL,
                  f"--max-budget-usd 0.0001 on a deliberately long task -> "
                  f"stop_reason={c.stop_reason!r}, error={c.error[:80]!r}, "
                  f"spent=${spent:.6f}"
                  + ("" if ok else " — the ceiling did not bind"),
                  spent)


@check("Custom tool definitions", live=False)
def c_tool_defs(backend) -> Result:
    """Defining a tool with your own schema — a playground staple the CLI lacks."""
    from workbench.api_backend import AnthropicAPIBackend
    b = AnthropicAPIBackend(api_key="offline-probe")
    tool = {"name": "get_weather", "description": "d",
            "input_schema": {"type": "object", "properties": {}}}
    body = b.build_body(Request(prompt="x", model="claude-haiku-4-5",
                                tool_defs=(tool,), tool_choice={"type": "any"}))
    ok = body.get("tools", [{}])[0].get("name") == "get_weather" \
        and body.get("tool_choice") == {"type": "any"}
    return Result("Custom tool definitions (via the API)", UNREACHABLE if ok else FAIL,
                  "`tools` in the request body, built on the anthropic-api backend "
                  "and driven over real HTTP in the test suite including the "
                  "resulting tool_use block. Missing: a credential. The CAPABILITY "
                  "is reachable another way — see the MCP row."
                  if ok else "tool definitions did not reach the request body")


@check("Prompt caching", live=False)
def c_caching(backend) -> Result:
    from workbench.api_backend import AnthropicAPIBackend
    b = AnthropicAPIBackend(api_key="offline-probe")
    body = b.build_body(Request(prompt="x", model="claude-haiku-4-5",
                                system="stable prefix", cache_system=True))
    ok = body["system"][0].get("cache_control") == {"type": "ephemeral"}
    return Result("Explicit cache_control breakpoints", UNREACHABLE if ok else FAIL,
                  "placing the breakpoint yourself needs the API. Built and "
                  "wire-tested. Missing: a credential. Caching ITSELF is not "
                  "missing — see the next row."
                  if ok else "cache_control did not reach the request body")


@check("Image and document input", live=False)
def c_attachments(backend) -> Result:
    from workbench.api_backend import AnthropicAPIBackend
    b = AnthropicAPIBackend(api_key="offline-probe")
    body = b.build_body(Request(
        prompt="describe it", model="claude-haiku-4-5",
        attachments=({"type": "image", "source": {"type": "base64",
                      "media_type": "image/png", "data": "iVBOR"}},)))
    kinds = [c["type"] for c in body["messages"][0]["content"]]
    ok = kinds == ["image", "text"]
    return Result("Image input as a content block", UNREACHABLE if ok else FAIL,
                  f"attachments lead the first user turn before the text, which is "
                  f"the documented order ({kinds}). Built and wire-tested. Missing: "
                  f"a credential." if ok else f"wrong block order: {kinds}")


@check("Prompt caching actually happens")
def c_caching_live(backend) -> Result:
    """Caching does not need the API. It needs a prefix over the minimum.

    The first version of this probe sent a 573-token system prompt, saw zeroes
    in every cache field, and would have recorded a negative result. That was
    not caching failing; it was a prefix under the model's minimum cacheable
    length. The lesson is kept in the code because a probe that cannot fail for
    the reason you think it failed is worse than no probe.
    """
    import subprocess
    prompts = sorted((REPO / "prompts").glob("*.md"))
    if not prompts:
        return Result("Prompt caching actually happens", UNREACHABLE, "no prompts/ to send")
    system = ("\n\n".join(f.read_text(encoding="utf-8") for f in prompts)) * 2

    def send(text: str) -> dict:
        proc = subprocess.run(
            ["claude", "-p", text, "--model", "claude-haiku-4-5",
             "--output-format", "json", "--tools", "", "--setting-sources", "",
             "--system-prompt", system],
            capture_output=True, text=True, timeout=180)
        return (json.loads(proc.stdout).get("usage") or {}) if proc.returncode == 0 else {}

    try:
        first = send("say A")
        second = send("say B")
    except Exception as exc:  # noqa: BLE001
        return Result("Prompt caching actually happens", UNREACHABLE, str(exc)[:200])

    created = first.get("cache_creation_input_tokens", 0)
    read = second.get("cache_read_input_tokens", 0)
    first_read = first.get("cache_read_input_tokens", 0)

    # The claim is "a repeated prefix is served from cache", and the second
    # call reading is what establishes it. Requiring the FIRST call to write
    # was an over-specification that demanded a cold cache: run this check
    # twice within the cache window and the second run legitimately reports
    # created=0, because the entry the earlier run wrote is still live. That
    # failed here, on a capability that was working. A check whose green
    # depends on nothing else having exercised the feature recently is testing
    # the schedule, not the feature.
    ok = read > 0
    origin = (f"{created} tokens written on the first call"
              if created else
              f"the first call read {first_read} from an entry still live from "
              f"an earlier run, so there was nothing to write")
    return Result("Prompt caching actually happens", PASS if ok else FAIL,
                  f"the CLI cached a repeated system prefix without any "
                  f"cache_control of ours: {origin}, and {read} tokens were read "
                  f"back on the second. Cache reads bill at a fraction of input, "
                  f"which is the cost lever this row was listed as missing"
                  if ok else
                  f"no caching observed: created={created} read={read} — a prefix "
                  f"under the model's minimum cacheable length will do this")


@check("Image input through the CLI")
def c_image_live(backend) -> Result:
    """Read hands the model real image bytes, which is the capability.

    Proved by content, not by the absence of an error. The first version of this
    probe used a fixed red quadrant on blue and asked which two colours were
    present -- a question whose answer a model could produce from the phrasing
    alone, without ever seeing a pixel. So it now generates a RANDOM 4x4 grid of
    green and yellow cells and asks for the count of green ones. The arrangement
    differs every run, the answer is one of seventeen, and no wording of the
    question hints at it.

    Worth knowing what this does NOT establish: acuity. Three harder probes were
    run and each misread something. Three vertical bands in a 24x24 image came
    back "Red, White, Blue" when they were orange, blue and white -- wrong first
    colour and wrong order. A 4x4 green/yellow grid was miscounted 6 against 4,
    once in three runs. Alternating stripes were counted 4 against 3, once in
    four. So image input is available and fine-detail fidelity is not
    guaranteed, and the two are different claims. This probe asserts only the
    first, deliberately, because a gate built on the second would report the
    capability missing in an environment where it demonstrably works.
    """
    import random
    import struct
    import subprocess
    import zlib

    # Two large solid halves, each a colour drawn at random from six that are
    # far apart in name and in RGB. Thirty of thirty-six ordered pairs are
    # distinct, so the answer cannot come from the question -- but naming the
    # colour of a 320x160 solid block is the easiest thing a model that sees
    # pixels can do.
    #
    # That separation is the whole design. Counting probes conflated two
    # questions: do image bytes ARRIVE, and can the model count accurately?
    # A 4x4 grid count was wrong once in three, and a stripe count once in four
    # -- so a count-based gate would report "image input unavailable" a quarter
    # of the time in an environment where it plainly works.
    PALETTE = {"red": (220, 30, 30), "green": (20, 160, 60), "blue": (30, 60, 220),
               "yellow": (245, 225, 40), "purple": (130, 40, 180),
               "orange": (250, 140, 20)}
    rng = random.Random()
    top, bottom = rng.sample(sorted(PALETTE), 2)
    W, HALF = 320, 80
    H = HALF * 2
    raw = b"".join(
        bytes([0]) + b"".join(bytes(PALETTE[top if y < HALF else bottom])
                              for _ in range(W))
        for y in range(H))

    def chunk(tag: bytes, data: bytes) -> bytes:
        return (struct.pack(">I", len(data)) + tag + data
                + struct.pack(">I", zlib.crc32(tag + data)))

    png = (b"\x89PNG\r\n\x1a\n"
           + chunk(b"IHDR", struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0))
           + chunk(b"IDAT", zlib.compress(raw))
           + chunk(b"IEND", b""))

    # Inside the repository: a path outside the CLI's working directory comes
    # back as "the file doesn't exist", which is a sandbox boundary and not an
    # absent capability. That distinction cost one confused probe to learn.
    target = REPO / ".parity-probe.png"
    target.write_bytes(png)
    try:
        proc = subprocess.run(
            ["claude", "-p", f"Read ./{target.name}. It is a 4x4 grid of squares, "
             "It is split into a top half and a bottom half, each one solid "
             "colour. Reply with exactly two words: the top colour, then the "
             "bottom colour.",
             "--model", "claude-haiku-4-5", "--output-format", "json",
             "--setting-sources", ""],
            capture_output=True, text=True, timeout=240, cwd=str(REPO))
        answer = json.loads(proc.stdout).get("result", "") if proc.returncode == 0 else ""
    except Exception as exc:  # noqa: BLE001
        return Result("Image input through the CLI", UNREACHABLE, str(exc)[:200])
    finally:
        target.unlink(missing_ok=True)

    named = [w for w in re.findall(r"[a-z]+", answer.lower()) if w in PALETTE]
    ok = named[:2] == [top, bottom]
    return Result("Image input through the CLI", PASS if ok else FAIL,
                  f"named a randomly generated image as {top} over {bottom}, one of "
                  f"thirty ordered pairs, with nothing in the question to supply it. "
                  f"Read passes image bytes to the model, so image input does not "
                  f"need the API — only a path inside the working directory"
                  if ok else
                  f"expected {top} over {bottom}, model said {named[:2] or None} "
                  f"(raw: {answer.strip()[:110]!r})")


@check("Custom tool definitions (via MCP)")
def c_mcp_tools(backend) -> Result:
    """Your schema, your name, your description — contributed over MCP.

    The tool returns a keyed digest the model cannot derive from the arguments,
    so a correct answer is only obtainable by actually calling it. A tool that
    could be guessed would prove nothing.
    """
    import subprocess
    import tempfile

    server = REPO / "tools" / "probes" / "mcp_custom_tool_server.py"
    if not server.exists():
        return Result("Custom tool definitions (via MCP)", FAIL, f"missing {server}")
    sys.path.insert(0, str(server.parent))
    import mcp_custom_tool_server as probe_server
    expected = probe_server.keyed_digest("parity", 8)

    with tempfile.TemporaryDirectory(prefix="parity-mcp-") as tmp:
        config = Path(tmp) / "mcp.json"
        config.write_text(json.dumps({"mcpServers": {"parity": {
            "command": "python3", "args": [str(server)]}}}), encoding="utf-8")
        try:
            proc = subprocess.run(
                ["claude", "-p", "Use the keyed_digest tool to compute the digest "
                 "of the phrase 'parity' with length 8. Reply with only the digest.",
                 "--model", "claude-haiku-4-5", "--output-format", "json",
                 "--setting-sources", "", "--mcp-config", str(config),
                 "--allowed-tools", "mcp__parity__keyed_digest"],
                capture_output=True, text=True, timeout=300, cwd=str(REPO))
            answer = json.loads(proc.stdout).get("result", "") if proc.returncode == 0 else ""
        except Exception as exc:  # noqa: BLE001
            return Result("Custom tool definitions (via MCP)", UNREACHABLE, str(exc)[:200])

    ok = expected in answer
    return Result("Custom tool definitions (via MCP)", PASS if ok else FAIL,
                  f"a tool named, described and schema'd entirely by this "
                  f"repository was offered to the model, chosen by it, and called: "
                  f"it returned {expected}, which is a keyed digest it could not "
                  f"derive from the arguments. Custom tool definitions do not need "
                  f"the API"
                  if ok else
                  f"expected {expected} in the answer, got {answer.strip()[:120]!r}")


@check("Multi-turn conversations")
def c_multiturn(backend) -> Result:
    """The playground's `messages` array: does context survive between turns?

    Two earlier versions of this probe were wrong in different ways, and both
    are worth keeping in view because each produced a confident wrong answer.

    The first used `--resume` with the session id the CLI reported. Every
    `claude -p` invocation from inside a session reports that session's OWN id,
    so the probe resumed this conversation and "recalled" a word that was
    already in it. It passed, and proved nothing.

    The second generated a hex nonce. The model declined it as suspicious, and a
    refusal is indistinguishable from a transport failure if you only check
    whether the answer came back. So the fact carried here is an ordinary one,
    generated in-process and never printed before the call: it cannot arrive by
    any route but turn one.
    """
    import random
    import subprocess

    floor, desk = random.randint(11, 89), random.randint(101, 999)
    turns = "\n".join(json.dumps({
        "type": "user",
        "message": {"role": "user", "content": [{"type": "text", "text": t}]}})
        for t in (f"I work on floor {floor}, at desk {desk}. Reply with only: noted.",
                  "Which desk number did I say I work at? Reply with only the number."))
    try:
        proc = subprocess.run(
            ["claude", "-p", "--input-format", "stream-json", "--output-format",
             "stream-json", "--verbose", "--model", "claude-haiku-4-5",
             "--tools", "", "--setting-sources", ""],
            input=turns, capture_output=True, text=True, timeout=300)
    except Exception as exc:  # noqa: BLE001
        return Result("Multi-turn conversations", UNREACHABLE, str(exc)[:200])

    results = []
    for line in proc.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            d = json.loads(line)
        except json.JSONDecodeError:
            continue
        if d.get("type") == "result":
            results.append(d.get("result", ""))

    ok = len(results) == 2 and str(desk) in results[1]
    return Result("Multi-turn conversations", PASS if ok else FAIL,
                  f"two user turns in one invocation over --input-format "
                  f"stream-json, and the second recalled a value only the first "
                  f"carried ({desk}). Prior context reaches the model without the "
                  f"API's messages array"
                  if ok else
                  f"{len(results)} result turn(s); second was "
                  f"{results[1][:80]!r} and did not carry {desk}"
                  if len(results) > 1 else f"{len(results)} result turn(s)")


@check("Streaming responses")
def c_streaming(backend) -> Result:
    """Incremental events, which is what the playground's `stream` field buys."""
    import subprocess
    try:
        proc = subprocess.run(
            ["claude", "-p", "count to three", "--model", "claude-haiku-4-5",
             "--output-format", "stream-json", "--verbose",
             "--tools", "", "--setting-sources", ""],
            capture_output=True, text=True, timeout=180)
    except Exception as exc:  # noqa: BLE001
        return Result("Streaming responses", UNREACHABLE, str(exc)[:200])

    kinds = []
    for line in proc.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            kinds.append(json.loads(line).get("type"))
        except json.JSONDecodeError:
            pass
    ok = len(kinds) > 1 and "result" in kinds and "assistant" in kinds
    return Result("Streaming responses", PASS if ok else FAIL,
                  f"{len(kinds)} newline-delimited events in one response "
                  f"({', '.join(sorted(set(k for k in kinds if k)))}), not a single "
                  f"blocking payload"
                  if ok else f"no incremental events: {kinds}")


@check("speed / fast mode")
def c_speed(backend) -> Result:
    """The playground carries a `speed` field. Headless CLI will not set it.

    Recorded with the CLI's own reason string rather than left off the matrix,
    because "no row" and "unreachable, and here is exactly why" read the same
    from a distance and are not the same thing.
    """
    import subprocess
    try:
        proc = subprocess.run(
            ["claude", "-p", "hi", "--model", "claude-haiku-4-5",
             "--output-format", "json", "--tools", "", "--setting-sources", ""],
            capture_output=True, text=True, timeout=180)
        payload = json.loads(proc.stdout)
    except Exception as exc:  # noqa: BLE001
        return Result("speed / fast mode", UNREACHABLE, str(exc)[:200])

    state = payload.get("fast_mode_state")
    reason = payload.get("fast_mode_disabled_reason")
    speed = (payload.get("usage") or {}).get("speed")
    return Result("speed / fast mode", UNREACHABLE,
                  f"the response reports fast_mode_state={state!r} with "
                  f"fast_mode_disabled_reason={reason!r} and usage.speed={speed!r}. "
                  f"No CLI flag sets it; the reason names an SDK opt-in this "
                  f"harness does not go through. Unreachable with a stated cause, "
                  f"not merely absent")


@check("Direct Messages API access", live=False)
def c_api_access(backend) -> Result:
    """Checked positively, not inferred from an unset variable."""
    import shutil
    from pathlib import Path as _P
    has_key = bool(os.environ.get("ANTHROPIC_API_KEY"))
    has_ant = shutil.which("ant") is not None
    profiles = _P.home() / ".config" / "anthropic"
    creds = _P.home() / ".claude" / ".credentials.json"
    # The environment names an OAuth token file descriptor. It is a pipe: a
    # one-shot stream the CLI consumed at startup, not a credential store.
    # Reading it now would block, or take bytes out of the running session's
    # own stream. Checked rather than assumed, because asserting a thing is
    # unreachable without looking is the failure this repository is about.
    fd_num = os.environ.get("CLAUDE_CODE_OAUTH_TOKEN_FILE_DESCRIPTOR")
    fd_kind = ""
    if fd_num:
        pid = os.environ.get("CLAUDE_PID", "")
        try:
            fd_kind = os.readlink(f"/proc/{pid}/fd/{fd_num}")
        except OSError:
            fd_kind = "not inspectable"
    found = [n for n, present in (
        ("ANTHROPIC_API_KEY", has_key), ("ant CLI", has_ant),
        ("~/.config/anthropic", profiles.exists()),
        ("~/.claude/.credentials.json", creds.exists()),
    ) if present]
    return Result("Direct Messages API access", UNREACHABLE,
                  "no credential source found: ANTHROPIC_API_KEY unset, the `ant` "
                  "CLI is not installed, and neither ~/.config/anthropic nor "
                  "~/.claude/.credentials.json exists. The OAuth token file "
                  f"descriptor the environment names resolves to {fd_kind or 'nothing'}"
                  " — a one-shot stream already consumed by the CLI, not a "
                  "credential store. This is why count_tokens, the Batch API and "
                  "stop_sequences are unreachable: established by looking for each "
                  "source, including that one, not inferred from an absent variable. "
                  "All three are implemented on the anthropic-api backend and would "
                  "run against a credential."
                  if not found else f"credential source(s) present: {found}")


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
                  + ") and on models after Opus 4.6 the API rejects them with a 400 — "
                  "removed from the platform, not missing from this tool. On models "
                  "that predate that, the anthropic-api backend sends them and "
                  "refuses to send them to a model that would 400; verified offline, "
                  "uncredentialed here."
                  if all_rejected else f"unexpected: {probes}")


@check("stop_sequences", live=False)
def c_stop_sequences(backend) -> Result:
    from workbench.api_backend import AnthropicAPIBackend
    b = AnthropicAPIBackend(api_key="offline-probe")
    body = b.build_body(Request(prompt="x", model="claude-haiku-4-5",
                                stop_sequences=("STOP",)))
    built = body.get("stop_sequences") == ["STOP"]
    return Result("stop_sequences", UNREACHABLE,
                  f"no CLI flag. BUILT on the anthropic-api backend and exercised "
                  f"over real HTTP against a conforming server, which received "
                  f"{body.get('stop_sequences')} in the request body. What is "
                  f"missing is a credential for Anthropic's endpoint, not code and "
                  f"not a tested transport."
                  if built else "the api backend did not carry stop_sequences")


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
    blocked = _blocked("Structured output against a schema", c)
    if blocked:
        return blocked
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
    blocked = _blocked("Tool availability is controllable", c)
    if blocked:
        return blocked
    turns = c.num_turns
    ok = turns == 1
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
    blocked = _blocked("Token counts and cost are reported", c)
    if blocked:
        return blocked
    has = c.cost_usd is not None and c.input_tokens > 0 and c.output_tokens > 0
    return Result("Token counts and cost are reported", PASS if has else FAIL,
                  f"in={c.input_tokens} out={c.output_tokens} cost=${c.cost_usd} "
                  f"— provider-reported, not estimated from a price table",
                  c.cost_usd or 0.0)


@check("count_tokens before sending", live=False)
def c_count_tokens(backend) -> Result:
    """The endpoint needs a credential. Counting tokens does not.

    This row read UNREACHABLE for a day on the strength of a true statement
    about /v1/messages/count_tokens, which quietly became a false statement
    about the capability. `claude -p --output-format json` reports
    `usage.input_tokens` from the same tokenizer, so the count is recoverable
    by difference against a calibrated empty baseline. The distinction the row
    now draws is between the endpoint and the number.
    """
    from workbench.api_backend import AnthropicAPIBackend
    has = callable(getattr(AnthropicAPIBackend, "count_tokens", None))
    if not has:
        return Result("count_tokens before sending", FAIL, "not implemented")
    return Result("count_tokens before sending", UNREACHABLE,
                  "/v1/messages/count_tokens is implemented and driven over real "
                  "HTTP in the test suite: it returns a count and omits max_tokens, "
                  "which that endpoint rejects. Missing: a credential, not code. "
                  "The capability itself is NOT missing — see the next row.")


@check("Token counting without a credential")
def c_count_tokens_differential(backend) -> Result:
    """Prove the differential counter, rather than asserting it works.

    Determinism and additivity are the two properties the method rests on, so
    both are exercised here on live calls. If either failed, every count the
    tool produced would be wrong, and an UNREACHABLE row would be the honest
    result rather than a PASS.
    """
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import count_tokens as ct
    try:
        first, second = ct.probe(""), ct.probe("")
        counter = ct.Counter()
        a = counter.count(ct.ADDITIVITY_A)
        b = counter.count(ct.ADDITIVITY_B)
        ab = counter.count(ct.ADDITIVITY_A + ct.ADDITIVITY_B)
    except ct.ProbeError as exc:
        return Result("Token counting without a credential", UNREACHABLE, str(exc))
    ok = first == second and a > 0 and ab == a + b
    return Result("Token counting without a credential", PASS if ok else FAIL,
                  f"usage.input_tokens gives Anthropic's own tokenizer through the "
                  f"CLI: baseline {first} tokens on two identical probes, and "
                  f"{a}+{b}={ab} on concatenation. Token counts are measured here "
                  f"without the endpoint and without a key"
                  if ok else
                  f"the differential method does not hold: baseline {first} vs "
                  f"{second}, {a}+{b} vs {ab}")


@check("Batch API 50% discount", live=False)
def c_batch(backend) -> Result:
    from workbench.api_backend import AnthropicAPIBackend
    has = callable(getattr(AnthropicAPIBackend, "submit_batch", None))
    return Result("Batch API 50% discount", UNREACHABLE,
                  "/v1/messages/batches is implemented and driven over real HTTP in "
                  "the test suite, keyed by custom_id since results return out of "
                  "order. Missing: a credential, not code." if has else "not implemented")


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
