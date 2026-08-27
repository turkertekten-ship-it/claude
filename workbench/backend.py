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

    prompt: str
    system: str | None = None
    append_system: str | None = None
    model: str | None = None
    effort: str | None = None
    tools: str | None = ""          # "" disables all tools
    json_schema: dict[str, Any] | None = None
    mode: str = "text"
    cwd: str | None = None
    max_budget_usd: float | None = None
    timeout_s: int = DEFAULT_TIMEOUT_S
    #: Bumped by the runner for repeat i of n, so repeats do not collide in the
    #: cache. Sampling is stochastic; repeats are the point.
    repeat: int = 0

    def cache_key(self) -> str:
        payload = {
            "prompt": self.prompt,
            "system": self.system,
            "append_system": self.append_system,
            "model": self.model,
            "effort": self.effort,
            "tools": self.tools,
            "json_schema": self.json_schema,
            "mode": self.mode,
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
        text = request.prompt
        if marker in request.prompt:
            start = request.prompt.index(marker) + len(marker)
            end = request.prompt.index("]]", start)
            text = request.prompt[start:end].strip()
        else:
            digest = hashlib.sha256(request.cache_key().encode()).hexdigest()[:8]
            text = f"echo({digest}): {request.prompt.strip()[:200]}"
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
        if request.json_schema:
            argv += ["--json-schema", json.dumps(request.json_schema)]
        if request.max_budget_usd is not None:
            argv += ["--max-budget-usd", str(request.max_budget_usd)]

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

    def complete(self, request: Request) -> Completion:
        argv = self._argv(request)
        started = time.time()
        try:
            proc = subprocess.run(
                argv,
                capture_output=True,
                text=True,
                timeout=request.timeout_s,
                cwd=request.cwd,
                env={**os.environ, "CLAUDE_CODE_ENTRYPOINT": "workbench"},
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
        try:
            envelope = json.loads(proc.stdout)
        except json.JSONDecodeError:
            return Completion(
                text=proc.stdout.strip(),
                error="backend did not return JSON; captured stdout as text",
                backend=self.name, duration_ms=elapsed_ms, workdir=request.cwd or "",
            )

        usage = envelope.get("usage") or {}
        model_usage = envelope.get("modelUsage") or envelope.get("model_usage") or {}
        model_name = next(iter(model_usage), request.model or "")
        error = ""
        if envelope.get("is_error"):
            error = str(envelope.get("subtype") or envelope.get("api_error_status")
                        or "backend reported is_error")

        return Completion(
            text=str(envelope.get("result", "")),
            structured=envelope.get("structured_output"),
            cost_usd=envelope.get("total_cost_usd"),
            input_tokens=int(usage.get("input_tokens") or 0),
            output_tokens=int(usage.get("output_tokens") or 0),
            cache_read_tokens=int(usage.get("cache_read_input_tokens") or 0),
            cache_creation_tokens=int(usage.get("cache_creation_input_tokens") or 0),
            duration_ms=int(envelope.get("duration_ms") or elapsed_ms),
            model=model_name,
            stop_reason=str(envelope.get("stop_reason") or ""),
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
        self.cache_dir = Path(cache_dir)
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
            self.hits += 1
            data = json.loads(path.read_text(encoding="utf-8"))
            return Completion(**data)
        self.misses += 1
        completion = self.inner.complete(request)
        if completion.ok:
            payload = asdict(completion)
            payload.pop("raw", None)
            path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        return completion


def resolve_backend(name: str, cache_dir: str | Path | None = None,
                    transcript: str | Path | None = None) -> Backend:
    """Build a backend by name, wrapping it in the disk cache when asked."""
    if name in ("claude", "claude-cli", "cli"):
        backend: Backend = ClaudeCLIBackend()
    elif name == "echo":
        backend = EchoBackend()
    elif name == "replay":
        if not transcript:
            raise BackendUnavailable("replay backend needs --transcript")
        backend = ReplayBackend(transcript)
    else:
        raise BackendUnavailable(
            f"unknown backend {name!r}; expected one of: claude-cli, echo, replay"
        )
    if cache_dir and name != "replay":
        backend = CachingBackend(backend, cache_dir)
    return backend
