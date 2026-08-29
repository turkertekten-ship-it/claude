"""Execution backends: the thing that actually turns a prompt into an answer.

This environment has no ``ANTHROPIC_API_KEY``, so the raw Messages API is not
reachable. What it does have is the Claude Code CLI itself, which in
``--print`` mode is a perfectly good completion engine and -- unlike a bare
API call -- reports its own cost.

Three backends, one interface:

``ClaudeCLIBackend``
    Shells out to ``claude -p --output-format json``. Real model, real cost.
    A workbench invocation deliberately strips the coding-agent surface --
    ``--tools ""``, ``--setting-sources ""``, an explicit ``--system-prompt``
    -- because the default Claude Code context is around thirty thousand
    tokens of tools and instructions that have nothing to do with the prompt
    under test. Measured on this container, that reduction took one identical
    call from $0.064242 to $0.001514.

``EchoBackend``
    Deterministic, free, offline. Tests run against this so the suite is
    hermetic and the test run costs nothing.

``ReplayBackend``
    Replays a recorded run from disk. This is what makes a published result
    checkable by someone who does not want to pay to re-run it.

Every backend returns the same :class:`Completion`, and every backend that
costs money reports the cost the provider charged rather than one this package
worked out from a price list. There is no price table in this repository on
purpose: a hard-coded price is a fact that goes stale without anyone noticing.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from .errors import BackendError, BackendUnavailable

DEFAULT_TIMEOUT_S = 300


@dataclass
class Completion:
    """One model response, plus everything needed to audit it."""

    text: str
    structured: Any = None
    #: Provider-reported cost. ``None`` means "this backend does not charge",
    #: which is not the same as zero-cost inference.
    cost_usd: float | None = None
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    cache_creation_tokens: int = 0
    duration_ms: int = 0
    model: str = ""
    stop_reason: str = ""
    num_turns: int = 1
    session_id: str = ""
    backend: str = ""
    error: str = ""
    #: Response headers, when the transport has any. The playground's run
    #: inspector shows these and they are not decoration: anthropic-ratelimit-*
    #: says how close a batch of runs is to being throttled, and request-id is
    #: the only handle support has on a specific call. The CLI shells out and
    #: never sees an HTTP response, so this stays empty there -- an honest
    #: empty, not a fabricated one.
    response_headers: dict[str, str] = field(default_factory=dict)
    #: The raw SSE text of a streaming call, verbatim. Matches the playground's
    #: rawSseText pane. Kept because a stream that reassembles wrongly cannot be
    #: debugged from the reassembled result -- that is the thing under suspicion.
    raw_stream: str = "" 
    #: The full backend envelope, kept so a surprising number can be traced.
    raw: dict[str, Any] = field(default_factory=dict)
    #: Populated in agent mode: the directory the run left behind.
    workdir: str = ""

    @property
    def ok(self) -> bool:
        return not self.error

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d.pop("raw", None)  # kept in the transcript file, not the summary
        return d


@dataclass(frozen=True)
class Request:
    """Everything that identifies one call, and therefore its cache key."""

    prompt: str = ""
    #: Successive user turns, for testing a conversation rather than a prompt.
    #: Assistant turns are not settable: prefill is rejected on current models,
    #: so what a multi-turn case controls is what the user says, and the model
    #: fills in the rest. When set, ``prompt`` is ignored.
    turns: tuple[str, ...] = ()
    system: str | None = None
    append_system: str | None = None
    model: str | None = None
    effort: str | None = None
    tools: str | None = ""          # "" disables all tools
    json_schema: dict[str, Any] | None = None
    mode: str = "text"
    #: `--thinking <mode>` and `--max-thinking-tokens <n>` are accepted by the
    #: CLI parser but absent from `--help`, so they were found by probing it
    #: rather than by reading it. Treated as real but undocumented: they may
    #: change without notice, which is why `doctor` labels them as such.
    thinking: str | None = None
    max_thinking_tokens: int | None = None
    #: There is no --max-tokens flag; the documented control is an env var.
    max_output_tokens: int | None = None
    #: Messages API only -- the CLI has no flag for any of these. Sampling
    #: parameters additionally 400 on models released after Claude Opus 4.6,
    #: which AnthropicAPIBackend refuses to send rather than letting the API
    #: reject them.
    stop_sequences: tuple[str, ...] = ()
    temperature: float | None = None
    top_p: float | None = None
    top_k: int | None = None
    #: Custom tool definitions, each {name, description, input_schema}. The CLI
    #: can only switch its own built-in tools on and off; defining a tool with
    #: your own schema and watching the model call it is a Messages API thing,
    #: and it is one of the things a playground is actually for.
    tool_defs: tuple[dict[str, Any], ...] = ()
    tool_choice: dict[str, Any] | None = None
    #: Cache the system prompt. A suite re-sends the same system prompt on
    #: every case; caching it is the single largest cost lever available.
    cache_system: bool = False
    #: Base64 image and document blocks, prepended to the first user turn.
    attachments: tuple[dict[str, Any], ...] = ()

    # -- the rest of the Messages API surface -------------------------------
    #: An audit found 12 of 24 documented parameters unimplemented. The
    #: playground's own description is that it "supports every Messages API
    #: parameter", so a workbench claiming parity with it needs them all.
    metadata: dict[str, Any] | None = None      # {"user_id": ...}
    stream: bool = False
    cache_request: bool = False                 # top-level auto-caching
    container: dict[str, Any] | None = None     # code execution / skills
    inference_geo: str | None = None
    service_tier: str | None = None
    mcp_servers: tuple[dict[str, Any], ...] = ()
    betas: tuple[str, ...] = ()
    fallbacks: Any = None                       # "default" or [{"model": ...}]
    context_management: dict[str, Any] | None = None
    speed: str | None = None                    # "fast"
    task_budget: dict[str, Any] | None = None
    thinking_budget: int | None = None
    thinking_display: str | None = None
    cwd: str | None = None
    max_budget_usd: float | None = None
    timeout_s: int = DEFAULT_TIMEOUT_S
    #: Bumped by the runner for repeat i of n, so repeats do not collide in the
    #: cache. Sampling is stochastic; repeats are the point.
    repeat: int = 0

    def cache_key(self) -> str:
        payload = {
            "prompt": self.prompt,
            "turns": list(self.turns),
            "system": self.system,
            "append_system": self.append_system,
            "model": self.model,
            "effort": self.effort,
            "tools": self.tools,
            "json_schema": self.json_schema,
            "mode": self.mode,
            "thinking": self.thinking,
            "max_thinking_tokens": self.max_thinking_tokens,
            "max_output_tokens": self.max_output_tokens,
            "stop_sequences": list(self.stop_sequences),
            "tool_defs": list(self.tool_defs),
            "tool_choice": self.tool_choice,
            "cache_system": self.cache_system,
            "attachments": list(self.attachments),
            "metadata": self.metadata, "stream": self.stream,
            "cache_request": self.cache_request, "container": self.container,
            "inference_geo": self.inference_geo, "service_tier": self.service_tier,
            "mcp_servers": list(self.mcp_servers), "betas": list(self.betas),
            "fallbacks": self.fallbacks, "context_management": self.context_management,
            "speed": self.speed, "task_budget": self.task_budget,
            "thinking_budget": self.thinking_budget,
            "thinking_display": self.thinking_display,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "top_k": self.top_k,
            # A spend ceiling changes what comes back -- a capped run can stop
            # early -- so it must key the cache. Omitting it meant two variants
            # differing only in their cap collided, and the second was served
            # the first's answer with --max-budget-usd never reaching the CLI.
            # A cache that silently ignores the field you are varying is the
            # same class of bug as the cross-backend collision that once served
            # 36 echo fixtures into a paid run.
            "max_budget_usd": self.max_budget_usd,
            "cwd": self.cwd,
            "repeat": self.repeat,
        }
        blob = json.dumps(payload, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:16]


class Backend:
    """Interface. Subclasses implement :meth:`complete`."""

    name = "abstract"
    charges_money = False

    def available(self) -> tuple[bool, str]:
        """Return ``(usable, reason)``. Reason is shown by ``workbench doctor``."""
        return True, "always available"

    def complete(self, request: Request) -> Completion:  # pragma: no cover
        raise NotImplementedError


class EchoBackend(Backend):
    """Deterministic stand-in. Free, offline, and reproducible.

    It answers with a stable transformation of the request so that graders,
    blinding and statistics can all be tested without spending anything or
    depending on a model's mood. Suites may steer it with a ``[[echo: ...]]``
    marker in the prompt, which is how test fixtures manufacture a specific
    output.
    """

    name = "echo"

    def complete(self, request: Request) -> Completion:
        marker = "[[echo:"
        # A multi-turn request is answered from its last turn, which is what a
        # real backend does too: earlier turns are context, the last one is the
        # thing being asked.
        source = request.turns[-1] if request.turns else request.prompt
        text = source
        if marker in source:
            start = source.index(marker) + len(marker)
            end = source.index("]]", start)
            text = source[start:end].strip()
        else:
            digest = hashlib.sha256(request.cache_key().encode()).hexdigest()[:8]
            text = f"echo({digest}): {source.strip()[:200]}"
        structured = None
        if request.json_schema:
            try:
                structured = json.loads(text)
            except json.JSONDecodeError:
                structured = None
        return Completion(
            text=text,
            structured=structured,
            cost_usd=0.0,
            input_tokens=len(request.prompt) // 4,
            output_tokens=len(text) // 4,
            model=request.model or "echo",
            stop_reason="end_turn",
            backend=self.name,
        )



def _fallback_model_names(fallbacks: Any) -> list[str]:
    """Model names from either shape `fallbacks` arrives in.

    The Messages API takes `[{"model": "..."}, ...]`; the CLI's
    --fallback-model takes a comma-separated list of names. A suite should not
    have to know which backend it will run against, so both are accepted, plus
    a plain string for the single-fallback case. The literal "default" is the
    API's own sentinel and names no model, so it is dropped rather than passed
    to the CLI as if it were one.
    """
    if not fallbacks or fallbacks == "default":
        return []
    if isinstance(fallbacks, str):
        return [fallbacks]
    names: list[str] = []
    for entry in fallbacks:
        if isinstance(entry, str):
            names.append(entry)
        elif isinstance(entry, dict) and entry.get("model"):
            names.append(str(entry["model"]))
    return names


class ClaudeCLIBackend(Backend):
    """The Claude Code CLI in ``--print`` mode, used as a completion engine."""

    name = "claude-cli"
    charges_money = True

    def __init__(self, executable: str = "claude", default_model: str | None = None):
        self.executable = executable
        self.default_model = default_model

    def available(self) -> tuple[bool, str]:
        path = shutil.which(self.executable)
        if not path:
            return False, f"{self.executable!r} is not on PATH"
        try:
            out = subprocess.run(
                [self.executable, "--version"],
                capture_output=True, text=True, timeout=30,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            return False, f"{path} would not run: {exc}"
        if out.returncode != 0:
            return False, f"{path} --version exited {out.returncode}"
        return True, f"{path} ({out.stdout.strip()})"

    def _argv(self, request: Request) -> list[str]:
        if request.turns:
            # Multi-turn needs the streaming transport in both directions, and
            # --verbose on top; the CLI refuses each of those combinations
            # separately, which is why this is a distinct argv shape rather
            # than one more flag on the single-prompt one.
            argv = [self.executable, "-p",
                    "--input-format", "stream-json",
                    "--output-format", "stream-json", "--verbose"]
            # The CLI's analogue of the playground's rawSseText pane. I said
            # last turn that the CLI "never sees an HTTP response, so it
            # reports these empty rather than inventing them" -- true of
            # response headers, and wrong about the stream:
            # --include-partial-messages emits the partial chunks as they
            # arrive, on exactly this transport. A stream that reassembles
            # wrongly cannot be debugged from the reassembled result.
            if request.stream:
                argv += ["--include-partial-messages"]
        else:
            argv = [self.executable, "-p", request.prompt, "--output-format", "json"]
        model = request.model or self.default_model
        if model:
            argv += ["--model", model]
        if request.system is not None:
            argv += ["--system-prompt", request.system]
        if request.append_system:
            argv += ["--append-system-prompt", request.append_system]
        if request.effort:
            argv += ["--effort", request.effort]
        # `fallbacks` was carried into the API body and dropped on the floor
        # here, though the CLI has --fallback-model for exactly this: automatic
        # fallback when the default model is overloaded or unavailable, as a
        # comma-separated list tried in order. A suite of 240 calls runs for
        # over an hour; an overload partway through kills the run and the money
        # already spent on it. Two of this session's runs cost $6-8 each.
        #
        # The API takes a list of objects; the CLI takes model names. Both
        # shapes are accepted here so a suite need not know which backend it
        # will meet.
        fallback_models = _fallback_model_names(request.fallbacks)
        if fallback_models:
            argv += ["--fallback-model", ",".join(fallback_models)]
        if request.json_schema:
            argv += ["--json-schema", json.dumps(request.json_schema)]
        if request.max_budget_usd is not None:
            argv += ["--max-budget-usd", str(request.max_budget_usd)]
        if request.thinking:
            argv += ["--thinking", request.thinking]
        if request.max_thinking_tokens is not None:
            argv += ["--max-thinking-tokens", str(request.max_thinking_tokens)]

        if request.mode == "text":
            # A prompt-engineering run should measure the prompt, not the
            # harness wrapped around it. Strip tools and inherited settings so
            # the model sees the system prompt under test and nothing else.
            argv += ["--tools", "", "--setting-sources", ""]
        else:
            # Agent mode: the artifact is the working directory, so tools are
            # the point. Permission prompts would hang a headless run.
            argv += ["--permission-mode", "bypassPermissions"]
            if request.tools:
                argv += ["--tools", request.tools]
        argv += ["--no-session-persistence"]
        return argv

    #: Environment variables withheld from an AGENT-mode child. Agent mode runs
    #: with --permission-mode bypassPermissions, because a permission prompt
    #: would hang a headless run -- so the model can execute whatever it likes
    #: inside the working directory. Handing that process the operator's tokens
    #: as well means a suite case that successfully induces a prompt injection
    #: gets host execution WITH credentials, and this repository's whole subject
    #: is prompts that try to make a model do the wrong thing.
    #:
    #: No suite sets `mode: agent` today, so nothing is currently exposed. That
    #: is the reason to do this now rather than after the first one lands.
    #: Text mode is unaffected: it runs with --tools "" and no permission bypass.
    AGENT_MODE_WITHHELD = (
        "GITHUB_TOKEN", "GH_TOKEN", "GITHUB_PAT",
        "ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN",
        "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_SESSION_TOKEN",
        "OPENAI_API_KEY", "SLACK_TOKEN", "NPM_TOKEN", "PYPI_TOKEN",
        "SSH_AUTH_SOCK", "GIT_ASKPASS", "GIT_TOKEN",
    )

    def _env(self, request: Request) -> dict[str, str]:
        env = {**os.environ, "CLAUDE_CODE_ENTRYPOINT": "workbench"}
        if request.mode == "agent":
            for name in self.AGENT_MODE_WITHHELD:
                env.pop(name, None)
            # Anything that merely LOOKS like a credential goes too. A withheld
            # list only covers the names someone thought of.
            for name in [k for k in env
                         if any(m in k.upper() for m in ("TOKEN", "SECRET", "PASSWORD",
                                                         "API_KEY", "APIKEY", "CREDENTIAL"))]:
                env.pop(name, None)
        if request.max_output_tokens is not None:
            env["CLAUDE_CODE_MAX_OUTPUT_TOKENS"] = str(request.max_output_tokens)
        return env

    @staticmethod
    def _stdin_for(request: Request) -> str | None:
        """NDJSON user turns, one per line, for the stream-json input format."""
        if not request.turns:
            return None
        return "\n".join(
            json.dumps({"type": "user", "message": {
                "role": "user", "content": [{"type": "text", "text": turn}]}})
            for turn in request.turns
        ) + "\n"

    @staticmethod
    def _last_result(stdout: str) -> dict[str, Any] | None:
        """The final ``result`` event in a stream.

        A multi-turn run emits one ``result`` per user turn. The last one is
        the answer to the last thing the user said, which is what the case is
        asking about; the earlier ones are intermediate.
        """
        final: dict[str, Any] | None = None
        for line in stdout.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            if event.get("type") == "result":
                final = event
        return final

    def complete(self, request: Request) -> Completion:
        argv = self._argv(request)
        started = time.time()
        try:
            proc = subprocess.run(
                argv,
                input=self._stdin_for(request),
                capture_output=True,
                text=True,
                timeout=request.timeout_s,
                cwd=request.cwd,
                env=self._env(request),
            )
        except subprocess.TimeoutExpired:
            return Completion(
                text="", error=f"timed out after {request.timeout_s}s",
                backend=self.name, duration_ms=int((time.time() - started) * 1000),
                workdir=request.cwd or "",
            )
        except OSError as exc:
            raise BackendError(f"could not launch {self.executable}: {exc}") from exc

        elapsed_ms = int((time.time() - started) * 1000)
        if not proc.stdout.strip():
            return Completion(
                text="", error=f"empty output (exit {proc.returncode}): "
                                f"{proc.stderr.strip()[:400]}",
                backend=self.name, duration_ms=elapsed_ms, workdir=request.cwd or "",
            )
        if request.turns:
            envelope = self._last_result(proc.stdout)
            if envelope is None:
                return Completion(
                    text="", error="no result event in the stream: "
                                   f"{proc.stderr.strip()[:300]}",
                    backend=self.name, duration_ms=elapsed_ms,
                    workdir=request.cwd or "",
                )
            completion = self._from_envelope(envelope, request, elapsed_ms)
            if request.stream:
                # The verbatim NDJSON the CLI emitted, including the partial
                # chunks --include-partial-messages adds. The CLI's answer to
                # the playground's rawSseText.
                completion.raw_stream = proc.stdout
            return completion
        try:
            envelope = json.loads(proc.stdout)
        except json.JSONDecodeError:
            return Completion(
                text=proc.stdout.strip(),
                error="backend did not return JSON; captured stdout as text",
                backend=self.name, duration_ms=elapsed_ms, workdir=request.cwd or "",
            )

        return self._from_envelope(envelope, request, elapsed_ms)

    def _from_envelope(self, envelope: dict[str, Any], request: Request,
                       elapsed_ms: int) -> Completion:
        usage = envelope.get("usage") or {}
        model_usage = envelope.get("modelUsage") or envelope.get("model_usage") or {}
        # `next(iter(...))` took whichever key happened to come first, and the CLI
        # reports its AUXILIARY model alongside the one that answered: asking for
        # claude-sonnet-5 returns modelUsage keyed
        # ['claude-haiku-4-5-20251001', 'claude-sonnet-5'], so every run in this
        # repository recorded haiku regardless of what it actually ran. The runs
        # were fine; the field describing them was not, and an acceptance check
        # reading that field concluded a two-family experiment had used one.
        #
        # Prefer the model that was ASKED for, then the one that did the most
        # generating, and only then fall back.
        model_name = ""
        if model_usage:
            asked = request.model or ""
            exact = [k for k in model_usage if k == asked]
            prefixed = [k for k in model_usage if asked and k.startswith(asked)]
            if exact or prefixed:
                model_name = (exact or prefixed)[0]
            else:
                def out_tokens(key: str) -> int:
                    entry = model_usage.get(key) or {}
                    return int(entry.get("outputTokens") or entry.get("output_tokens") or 0)
                model_name = max(model_usage, key=out_tokens)
        model_name = model_name or request.model or ""
        error = ""
        if envelope.get("is_error"):
            # `subtype` is often the useless string "success" even on an error
            # envelope, so prefer anything that actually describes the failure.
            error = str(envelope.get("api_error_status")
                        or str(envelope.get("result", ""))[:300]
                        or envelope.get("subtype")
                        or "backend reported is_error")

        text = str(envelope.get("result", ""))
        stop_reason = str(envelope.get("stop_reason") or "")
        # The CLI has no --stop-sequences flag, so the request field was
        # accepted and silently ignored: a suite could set it and get output
        # straight through it, with nothing saying so. Applied here instead.
        #
        # This is NOT what the API does and the difference is worth stating.
        # The API stops GENERATING at the sequence and bills only what it
        # produced; this truncates text already generated and paid for. The
        # visible behaviour matches, the economics do not, and stop_reason is
        # set to "stop_sequence" so a reader can tell which happened.
        if request.stop_sequences and text:
            cut = min((i for i in (text.find(q) for q in request.stop_sequences)
                       if i >= 0), default=-1)
            if cut >= 0:
                text = text[:cut]
                stop_reason = "stop_sequence"

        return Completion(
            text=text,
            structured=envelope.get("structured_output"),
            cost_usd=envelope.get("total_cost_usd"),
            input_tokens=int(usage.get("input_tokens") or 0),
            output_tokens=int(usage.get("output_tokens") or 0),
            cache_read_tokens=int(usage.get("cache_read_input_tokens") or 0),
            cache_creation_tokens=int(usage.get("cache_creation_input_tokens") or 0),
            duration_ms=int(envelope.get("duration_ms") or elapsed_ms),
            model=model_name,
            stop_reason=stop_reason,
            num_turns=int(envelope.get("num_turns") or 1),
            session_id=str(envelope.get("session_id") or ""),
            backend=self.name,
            error=error,
            raw=envelope,
            workdir=request.cwd or "",
        )


class ReplayBackend(Backend):
    """Serve completions from a recorded run, so a result can be re-checked free.

    Misses are an error rather than a silent live call: a replay that quietly
    falls through to the network is not a replay, and the difference would
    show up only on the invoice.
    """

    name = "replay"

    def __init__(self, transcript: str | Path):
        self.path = Path(transcript)
        if not self.path.exists():
            raise BackendUnavailable(f"no transcript at {self.path}")
        self._by_key: dict[str, dict[str, Any]] = {}
        for line in self.path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            record = json.loads(line)
            if "cache_key" in record:
                self._by_key[record["cache_key"]] = record

    def available(self) -> tuple[bool, str]:
        return bool(self._by_key), f"{len(self._by_key)} recorded completion(s)"

    def complete(self, request: Request) -> Completion:
        key = request.cache_key()
        record = self._by_key.get(key)
        if record is None:
            raise BackendError(
                f"replay miss for {key}: this request was not in "
                f"{self.path}. Re-record rather than falling through to a "
                f"live call."
            )
        payload = dict(record.get("completion") or {})
        payload.pop("raw", None)
        return Completion(**payload)


class CachingBackend(Backend):
    """Memoises an inner backend on disk, keyed by the full request.

    A sweep re-runs the same prompt against five configurations; four of them
    usually differ in one field. Without this, an interrupted sweep restarts
    from zero and pays twice.
    """

    def __init__(self, inner: Backend, cache_dir: str | Path):
        self.inner = inner
        # Per-backend directory, not a shared one. The request hash covers the
        # prompt and the configuration but says nothing about WHO answered, so
        # a single flat cache will happily serve an EchoBackend fixture to a
        # live run. That is not hypothetical: it happened here, and 36 echo
        # fixtures were served into a $3 measurement before the outputs were
        # read closely enough to notice.
        self.cache_dir = Path(cache_dir) / inner.name
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.hits = 0
        self.misses = 0

    @property
    def name(self) -> str:  # type: ignore[override]
        return f"cached:{self.inner.name}"

    @property
    def charges_money(self) -> bool:  # type: ignore[override]
        return self.inner.charges_money

    def available(self) -> tuple[bool, str]:
        return self.inner.available()

    def complete(self, request: Request) -> Completion:
        # Agent-mode runs mutate a working directory; their value is not in the
        # text alone, so caching them would hand back a stale filesystem.
        if request.mode == "agent":
            return self.inner.complete(request)
        path = self.cache_dir / f"{request.cache_key()}.json"
        if path.exists():
            # A truncated or corrupt entry used to raise JSONDecodeError out of
            # complete() forever: the run that was interrupted mid-write poisoned
            # that key permanently, and every later run died on it. A cache is an
            # optimisation, so an unreadable entry is a miss, not a fatal error.
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError, OSError):
                data = None
                path.unlink(missing_ok=True)
            if isinstance(data, dict):
                if data.get("backend") == self.inner.name:
                    try:
                        completion = Completion(**data)
                    except TypeError:
                        # Written by an older schema. Discard and re-fetch
                        # rather than crash.
                        path.unlink(missing_ok=True)
                    else:
                        self.hits += 1
                        return completion
                else:
                    # Someone else's answer. Ignore it rather than reporting it
                    # as ours.
                    path.unlink(missing_ok=True)
        self.misses += 1
        completion = self.inner.complete(request)
        if completion.ok:
            payload = asdict(completion)
            payload.pop("raw", None)
            # Write to a unique temp file in the same directory, then rename.
            # rename is atomic within a filesystem, so a reader never sees a
            # half-written entry and two concurrent writers cannot interleave.
            tmp = path.with_name(f"{path.stem}.{os.getpid()}.tmp")
            try:
                tmp.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
                tmp.replace(path)
            except OSError:
                tmp.unlink(missing_ok=True)   # a cache write must never fail a run
        return completion


def resolve_backend(name: str, cache_dir: str | Path | None = None,
                    transcript: str | Path | None = None) -> Backend:
    """Build a backend by name, wrapping it in the disk cache when asked."""
    if name in ("api", "anthropic-api", "messages"):
        from .api_backend import AnthropicAPIBackend
        backend: Backend = AnthropicAPIBackend()
    elif name in ("claude", "claude-cli", "cli"):
        backend = ClaudeCLIBackend()
    elif name == "echo":
        backend = EchoBackend()
    elif name == "replay":
        if not transcript:
            raise BackendUnavailable("replay backend needs --transcript")
        backend = ReplayBackend(transcript)
    else:
        raise BackendUnavailable(
            f"unknown backend {name!r}; expected one of: claude-cli, "
            f"anthropic-api, echo, replay"
        )
    if cache_dir and name != "replay":
        backend = CachingBackend(backend, cache_dir)
    return backend
