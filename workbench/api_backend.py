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
            body["system"] = request.system
        if request.stop_sequences:
            body["stop_sequences"] = list(request.stop_sequences)
        if request.effort:
            body["output_config"] = {"effort": request.effort}
        if request.json_schema:
            body.setdefault("output_config", {})["format"] = {
                "type": "json_schema", "schema": request.json_schema,
            }
        if request.thinking:
            body["thinking"] = {"type": request.thinking}

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

    def _post(self, path: str, body: dict[str, Any], timeout: int = 300) -> dict[str, Any]:
        if not self.api_key:
            raise BackendUnavailable(find_credential()[1])
        req = urllib.request.Request(
            f"{self.base_url}{path}",
            data=json.dumps(body).encode("utf-8"),
            headers={"content-type": "application/json",
                     "anthropic-version": API_VERSION,
                     "x-api-key": self.api_key},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")[:400]
            raise BackendError(f"{path} returned {exc.code}: {detail}") from exc
        except urllib.error.URLError as exc:
            raise BackendError(f"{path} unreachable: {exc.reason}") from exc

    # -- the interface -------------------------------------------------------

    def complete(self, request: Request) -> Completion:
        started = time.time()
        envelope = self._post("/v1/messages", self.build_body(request),
                              timeout=request.timeout_s)
        return self.parse(envelope, int((time.time() - started) * 1000))

    @staticmethod
    def parse(envelope: dict[str, Any], elapsed_ms: int = 0) -> Completion:
        """Map a Messages API response onto a Completion.

        Cost is left as ``None``: this endpoint reports tokens, not money, and
        turning tokens into dollars needs a price table. There is no price
        table in this repository, because a hard-coded price goes stale without
        anyone noticing.
        """
        text = "".join(block.get("text", "") for block in envelope.get("content", [])
                       if block.get("type") == "text")
        usage = envelope.get("usage") or {}
        return Completion(
            text=text,
            structured=envelope.get("parsed"),
            cost_usd=None,
            input_tokens=int(usage.get("input_tokens") or 0),
            output_tokens=int(usage.get("output_tokens") or 0),
            cache_read_tokens=int(usage.get("cache_read_input_tokens") or 0),
            cache_creation_tokens=int(usage.get("cache_creation_input_tokens") or 0),
            duration_ms=elapsed_ms,
            model=str(envelope.get("model") or ""),
            stop_reason=str(envelope.get("stop_reason") or ""),
            backend=AnthropicAPIBackend.name,
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
