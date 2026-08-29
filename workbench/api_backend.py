"""A direct Messages API backend, for the capabilities the CLI cannot reach.

Five things a playground does that `claude -p` has no flag for: `stop_sequences`,
an exact `max_tokens`, counting tokens before sending, submitting a batch at half
price, and setting `temperature` on a model old enough to still accept it. All
five are Messages API parameters. None of them is missing from this package for
want of code — they are missing for want of a credential.

So the code is here. In this container it does not run: there is no
`ANTHROPIC_API_KEY`, no `ant` CLI, no `~/.config/anthropic` and no
`~/.claude/.credentials.json`, each checked rather than assumed. `workbench
doctor` says so, and says it in those terms — **implemented, uncredentialed** —
because "we did not build it" and "this machine cannot run it" are different
statements and only one of them is a gap in the tool.

Everything that does not need the network is tested: request construction, the
deprecation rules, response parsing, and the refusal to send a parameter the
target model will reject. What is untested is the wire, and that is stated
rather than glossed.

Standard library only, per the house rules -- `urllib.request`, not `requests`.
"""

from __future__ import annotations

import json
import os
import shutil
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from .backend import Backend, Completion, Request
from .errors import BackendError, BackendUnavailable

API_BASE = os.environ.get("ANTHROPIC_BASE_URL", "https://api.anthropic.com")
API_VERSION = "2023-06-01"

#: Models released after Claude Opus 4.6 reject `temperature`, `top_p` and
#: `top_k` outright, so sending one is a 400 rather than a nuance. Anything
#: listed here still accepts them; anything else does not.
SAMPLING_OK = ("claude-opus-4-6", "claude-sonnet-4-6", "claude-opus-4-5",
               "claude-sonnet-4-5", "claude-haiku-4-5", "claude-3")


def sampling_allowed(model: str) -> bool:
    """Does this model still accept temperature / top_p / top_k?"""
    return any(model.startswith(prefix) for prefix in SAMPLING_OK)


def find_credential() -> tuple[str | None, str]:
    """Locate an API credential, or say precisely what was looked for.

    Returns ``(key, description)``. A missing credential is reported by naming
    every place that was checked, because "not set" and "not looked for" read
    identically in a report and only one of them is honest.
    """
    key = os.environ.get("ANTHROPIC_API_KEY")
    if key:
        return key, "ANTHROPIC_API_KEY"
    checked = ["ANTHROPIC_API_KEY (unset)"]

    if shutil.which("ant"):
        return None, "the `ant` CLI is installed; run `ant auth print-credentials --access-token`"
    checked.append("`ant` CLI (not installed)")

    for path in (Path.home() / ".config" / "anthropic",
                 Path.home() / ".claude" / ".credentials.json"):
        checked.append(f"{path} ({'present' if path.exists() else 'absent'})")
        if path.exists():
            return None, f"a credential store exists at {path} but this backend does not read it"

    return None, "no credential found — checked " + ", ".join(checked)


class AnthropicAPIBackend(Backend):
    """The Messages API, reached directly."""

    name = "anthropic-api"
    charges_money = True

    def __init__(self, api_key: str | None = None, base_url: str = API_BASE):
        self.api_key = api_key or find_credential()[0]
        self.base_url = base_url.rstrip("/")

    def available(self) -> tuple[bool, str]:
        if self.api_key:
            return True, f"credential present; {self.base_url}"
        return False, find_credential()[1]

    # -- request construction ------------------------------------------------

    def build_body(self, request: Request) -> dict[str, Any]:
        """Turn a Request into a Messages API body.

        Refuses to send a sampling parameter to a model that will reject it,
        rather than letting the API return a 400 the caller has to decode.
        """
        model = request.model or "claude-haiku-4-5"
        body: dict[str, Any] = {
            "model": model,
            "max_tokens": request.max_output_tokens or 4096,
            "messages": [{"role": "user", "content": turn}
                         for turn in (request.turns or (request.prompt,))],
        }
        if request.system:
            if request.cache_system:
                # A suite sends the same system prompt on every case. Marking it
                # cacheable is the largest cost lever the API offers, and the
                # response reports whether it worked -- cache_read_input_tokens
                # staying at zero across repeated calls means something in the
                # prefix is changing.
                body["system"] = [{"type": "text", "text": request.system,
                                   "cache_control": {"type": "ephemeral"}}]
            else:
                body["system"] = request.system

        if request.tool_defs:
            body["tools"] = [dict(t) for t in request.tool_defs]
            if request.tool_choice:
                body["tool_choice"] = dict(request.tool_choice)

        if request.attachments:
            # Images and documents ride in the first user turn, before the text,
            # which is the order the docs specify.
            first = body["messages"][0]
            first["content"] = [dict(a) for a in request.attachments] + [
                {"type": "text", "text": first["content"]}
            ]
        if request.stop_sequences:
            body["stop_sequences"] = list(request.stop_sequences)
        if request.effort:
            body["output_config"] = {"effort": request.effort}
        if request.json_schema:
            body.setdefault("output_config", {})["format"] = {
                "type": "json_schema", "schema": request.json_schema,
            }
        if request.thinking:
            thinking: dict[str, Any] = {"type": request.thinking}
            # budget_tokens is removed on Fable 5, Opus 5/4.8/4.7 and Sonnet 5,
            # and deprecated on 4.6. It is sent only when asked for, and only
            # with the mode that still accepts it.
            if request.thinking_budget is not None and request.thinking == "enabled":
                thinking["budget_tokens"] = request.thinking_budget
            if request.thinking_display:
                thinking["display"] = request.thinking_display
            body["thinking"] = thinking

        # The remaining Messages API surface. Each is sent only when set, so a
        # request stays minimal and a server that does not know a parameter is
        # never handed one.
        for field, key in (("metadata", "metadata"),
                           ("container", "container"),
                           ("inference_geo", "inference_geo"),
                           ("service_tier", "service_tier"),
                           ("fallbacks", "fallbacks"),
                           ("context_management", "context_management"),
                           ("speed", "speed")):
            value = getattr(request, field)
            if value is not None:
                body[key] = value
        if request.stream:
            body["stream"] = True
        if request.cache_request:
            body["cache_control"] = {"type": "ephemeral"}
        if request.mcp_servers:
            # The connector needs both halves: the server list, and a toolset
            # entry in `tools` naming each server. Sending one without the other
            # is a validation error, so the toolset is added here rather than
            # left to the caller to remember.
            body["mcp_servers"] = [dict(m) for m in request.mcp_servers]
            toolsets = [{"type": "mcp_toolset", "mcp_server_name": m["name"]}
                        for m in request.mcp_servers]
            body["tools"] = list(body.get("tools", [])) + toolsets
        if request.task_budget:
            body.setdefault("output_config", {})["task_budget"] = request.task_budget

        sampling = {k: v for k, v in (("temperature", request.temperature),
                                      ("top_p", request.top_p),
                                      ("top_k", request.top_k)) if v is not None}
        if sampling:
            if not sampling_allowed(model):
                raise BackendError(
                    f"{model} rejects {', '.join(sampling)} with a 400: models "
                    f"released after Claude Opus 4.6 do not accept sampling "
                    f"parameters. Use a model that predates that, or drop them."
                )
            body.update(sampling)
        return body

    def _headers(self, betas: tuple[str, ...] = ()) -> dict[str, str]:
        headers = {"content-type": "application/json",
                   "anthropic-version": API_VERSION,
                   "x-api-key": self.api_key or ""}
        if betas:
            headers["anthropic-beta"] = ",".join(betas)
        return headers

    def _post(self, path: str, body: dict[str, Any], timeout: int = 300,
              betas: tuple[str, ...] = ()) -> dict[str, Any]:
        if not self.api_key:
            raise BackendUnavailable(find_credential()[1])
        req = urllib.request.Request(
            f"{self.base_url}{path}",
            data=json.dumps(body).encode("utf-8"),
            headers=self._headers(betas),
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as response:
                envelope = json.loads(response.read().decode("utf-8"))
                if isinstance(envelope, dict):
                    envelope["_response_headers"] = dict(response.headers.items())
                return envelope
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")[:400]
            raise BackendError(f"{path} returned {exc.code}: {detail}") from exc
        except urllib.error.URLError as exc:
            raise BackendError(f"{path} unreachable: {exc.reason}") from exc

    # -- the interface -------------------------------------------------------

    def complete(self, request: Request) -> Completion:
        started = time.time()
        if request.stream:
            envelope = self._stream("/v1/messages", self.build_body(request),
                                    request.timeout_s, request.betas)
        else:
            envelope = self._post("/v1/messages", self.build_body(request),
                                  timeout=request.timeout_s, betas=request.betas)
        return self.parse(envelope, int((time.time() - started) * 1000))

    def _stream(self, path: str, body: dict[str, Any], timeout: int,
                betas: tuple[str, ...]) -> dict[str, Any]:
        """Consume a server-sent event stream and rebuild the final message.

        Streaming is required for large `max_tokens` -- the SDKs refuse a
        non-streaming request above roughly 21k -- so a workbench that cannot
        stream cannot exercise the long-output end of the parameter space at
        all. The deltas are reassembled into the same envelope shape a
        non-streaming call returns, so nothing downstream has to know which
        path was taken.
        """
        if not self.api_key:
            raise BackendUnavailable(find_credential()[1])
        req = urllib.request.Request(
            f"{self.base_url}{path}", data=json.dumps(body).encode("utf-8"),
            headers=self._headers(betas), method="POST")
        envelope: dict[str, Any] = {"content": [], "usage": {}}
        sse_lines: list[str] = []
        try:
            with urllib.request.urlopen(req, timeout=timeout) as response:
                envelope["_response_headers"] = dict(response.headers.items())
                for raw in response:
                    decoded = raw.decode("utf-8")
                    sse_lines.append(decoded)
                    line = decoded.strip()
                    if not line.startswith("data:"):
                        continue
                    payload = line[5:].strip()
                    if not payload or payload == "[DONE]":
                        continue
                    event = json.loads(payload)
                    kind = event.get("type")
                    if kind == "message_start":
                        message = event.get("message", {})
                        envelope.update({k: v for k, v in message.items()
                                         if k != "content"})
                        envelope["usage"] = dict(message.get("usage") or {})
                        envelope["content"] = []
                    elif kind == "content_block_start":
                        envelope["content"].append(dict(event.get("content_block") or {}))
                    elif kind == "content_block_delta":
                        delta = event.get("delta") or {}
                        if envelope["content"]:
                            block = envelope["content"][-1]
                            dt = delta.get("type")
                            if dt == "input_json_delta":
                                # Tool arguments stream as partial JSON. Only
                                # `text` was accumulated, so every tool call made
                                # over a streaming request arrived with input={}
                                # -- the arguments silently discarded.
                                block["_partial_json"] = (
                                    block.get("_partial_json", "") + (delta.get("partial_json") or ""))
                            elif dt == "thinking_delta":
                                block["thinking"] = (
                                    block.get("thinking", "") + (delta.get("thinking") or ""))
                            elif dt == "signature_delta":
                                block["signature"] = (
                                    block.get("signature", "") + (delta.get("signature") or ""))
                            else:
                                block["text"] = block.get("text", "") + (delta.get("text") or "")
                    elif kind == "content_block_stop":
                        # Parse the accumulated tool arguments once the block
                        # closes; a partial fragment is not valid JSON.
                        if envelope["content"]:
                            block = envelope["content"][-1]
                            raw_json = block.pop("_partial_json", None)
                            if raw_json is not None:
                                try:
                                    block["input"] = json.loads(raw_json) if raw_json.strip() else {}
                                except json.JSONDecodeError:
                                    block["input"] = {}
                                    block["_unparsed_input"] = raw_json[:500]
                    elif kind == "message_delta":
                        envelope.update(event.get("delta") or {})
                        envelope["usage"].update(event.get("usage") or {})
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")[:400]
            raise BackendError(f"{path} returned {exc.code}: {detail}") from exc
        except urllib.error.URLError as exc:
            raise BackendError(f"{path} unreachable: {exc.reason}") from exc
        envelope["_raw_stream"] = "".join(sse_lines)
        return envelope

    @staticmethod
    def parse(envelope: dict[str, Any], elapsed_ms: int = 0) -> Completion:
        """Map a Messages API response onto a Completion.

        Cost is left as ``None``: this endpoint reports tokens, not money, and
        turning tokens into dollars needs a price table. There is no price
        table in this repository, because a hard-coded price goes stale without
        anyone noticing.
        """
        blocks = envelope.get("content", [])
        text = "".join(b.get("text", "") for b in blocks if b.get("type") == "text")
        tool_calls = [{"name": b.get("name"), "input": b.get("input"), "id": b.get("id")}
                      for b in blocks if b.get("type") == "tool_use"]
        usage = envelope.get("usage") or {}
        return Completion(
            text=text,
            structured=envelope.get("parsed") or (tool_calls or None),
            cost_usd=None,
            input_tokens=int(usage.get("input_tokens") or 0),
            output_tokens=int(usage.get("output_tokens") or 0),
            cache_read_tokens=int(usage.get("cache_read_input_tokens") or 0),
            cache_creation_tokens=int(usage.get("cache_creation_input_tokens") or 0),
            duration_ms=elapsed_ms,
            model=str(envelope.get("model") or ""),
            stop_reason=str(envelope.get("stop_reason") or ""),
            backend=AnthropicAPIBackend.name,
            # The playground's run inspector shows stopReason, responseHeaders
            # and rawSseText together, and the first was the only one of the
            # three this backend carried.
            response_headers=dict(envelope.get("_response_headers") or {}),
            raw_stream=str(envelope.get("_raw_stream") or ""),
            raw=envelope,
        )

    # -- the capabilities the CLI has no flag for ----------------------------

    def count_tokens(self, request: Request) -> int:
        """`POST /v1/messages/count_tokens` — what a prompt costs before sending it."""
        body = self.build_body(request)
        body.pop("max_tokens", None)
        payload = self._post("/v1/messages/count_tokens", body, timeout=60)
        return int(payload.get("input_tokens", 0))

    def submit_batch(self, requests: list[tuple[str, Request]]) -> str:
        """`POST /v1/messages/batches` — the same work at half price, asynchronously.

        Returns the batch id. Results arrive out of order and are matched by
        ``custom_id``, never by position.
        """
        body = {"requests": [{"custom_id": cid, "params": self.build_body(r)}
                             for cid, r in requests]}
        return str(self._post("/v1/messages/batches", body, timeout=120)["id"])
