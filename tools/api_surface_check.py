#!/usr/bin/env python3
"""Check the API backend against the documented request surface.

"Is the parity matrix complete?" was, three times running, a question only
answerable by noticing something missing several turns after writing it down.
Tool definitions were miscounted as covered by a CLI flag; prompt caching and
image input were absent from the matrix entirely; then twelve parameters turned
out to be unimplemented. Every one of those was found by re-reading the API,
never by a mechanism.

This is the mechanism. `docs/messages-api-surface.yaml` records the documented
parameters and where the list came from; this diffs that against what
`AnthropicAPIBackend.build_body` actually emits when handed a maximal request.

It cannot notice a parameter the docs gained after the snapshot was taken —
nothing here can, short of fetching at test time and failing on a network
blip. What it can do is make the snapshot the thing that goes stale, which is
visible and fixable, rather than a belief, which is neither.

Usage:
    python3 tools/api_surface_check.py           # 0 complete, 1 gaps
    python3 tools/api_surface_check.py --json

Exit: 0 every documented parameter is reachable, 1 some are not, 2 cannot run.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

import yaml  # noqa: E402

from workbench.api_backend import AnthropicAPIBackend  # noqa: E402
from workbench.backend import Request  # noqa: E402

SURFACE = REPO / "docs" / "messages-api-surface.yaml"

#: A request exercising every parameter at once. Anything the backend can emit
#: appears in the body built from this; anything missing from the body is
#: something a suite author cannot reach.
MAXIMAL = Request(
    prompt="probe", model="claude-opus-4-6", system="s",
    max_output_tokens=64, stop_sequences=("STOP",), temperature=0.5,
    top_p=0.99, top_k=5, effort="high", json_schema={"type": "object"},
    thinking="enabled", thinking_budget=1024, thinking_display="summarized",
    tool_defs=({"name": "t", "description": "d", "input_schema": {}},),
    tool_choice={"type": "auto"}, cache_request=True,
    attachments=({"type": "image", "source": {}},),
    metadata={"user_id": "u"}, stream=True, container={"skills": []},
    inference_geo="us", service_tier="auto",
    mcp_servers=({"type": "url", "url": "u", "name": "n"},),
    betas=("fast-mode-2026-02-01",), fallbacks="default",
    context_management={"edits": []}, speed="fast",
    task_budget={"type": "tokens", "total": 20000},
)

#: Parameters that legitimately live somewhere other than a top-level body key.
ELSEWHERE = {
    "betas": "the anthropic-beta header",
    "task_budget": "nested inside output_config",
}


def emitted() -> tuple[set[str], dict[str, str]]:
    """What the backend actually puts on the wire, and where."""
    backend = AnthropicAPIBackend(api_key="surface-probe")
    body = backend.build_body(MAXIMAL)
    keys = set(body)
    where = {k: "request body" for k in keys}

    if "task_budget" in (body.get("output_config") or {}):
        keys.add("task_budget")
        where["task_budget"] = "output_config.task_budget"
    if backend._headers(MAXIMAL.betas).get("anthropic-beta"):
        keys.add("betas")
        where["betas"] = "anthropic-beta header"
    return keys, where


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv[1:])

    if not SURFACE.is_file():
        print(f"api_surface_check: no snapshot at {SURFACE}", file=sys.stderr)
        return 2
    snapshot = yaml.safe_load(SURFACE.read_text(encoding="utf-8"))
    ga = list(snapshot.get("ga") or [])
    beta = list((snapshot.get("beta") or {}).keys())

    keys, where = emitted()
    missing_ga = [p for p in ga if p not in keys]
    missing_beta = [p for p in beta if p not in keys]

    if args.json:
        print(json.dumps({
            "source": snapshot.get("source"), "fetched": snapshot.get("fetched"),
            "ga": {"total": len(ga), "covered": len(ga) - len(missing_ga),
                   "missing": missing_ga},
            "beta": {"total": len(beta), "covered": len(beta) - len(missing_beta),
                     "missing": missing_beta},
        }, indent=2))
        return 1 if missing_ga else 0

    print("Messages API request surface — snapshot against implementation")
    print("=" * 68)
    print(f"snapshot: {snapshot.get('source')} (fetched {snapshot.get('fetched')})")
    print()
    for name in ga:
        mark = "ok  " if name in keys else "MISS"
        note = ELSEWHERE.get(name, "")
        print(f"  [{mark}] {name}" + (f"   ({where.get(name, note)})" if note else ""))
    print()
    print(f"generally available: {len(ga) - len(missing_ga)}/{len(ga)} reachable")
    print(f"beta parameters    : {len(beta) - len(missing_beta)}/{len(beta)} reachable"
          f"  ({', '.join(beta)})")
    if missing_ga:
        print(f"\nMISSING: {', '.join(missing_ga)}")
        print("Each is a parameter a suite author cannot reach.")
    else:
        print("\nEvery documented parameter in the snapshot is reachable from a "
              "Request.\nThis says nothing about parameters the API gained after "
              f"{snapshot.get('fetched')} — re-fetch the surface to find those.")
    return 1 if missing_ga else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
