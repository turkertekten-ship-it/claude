#!/usr/bin/env python3
"""A minimal MCP server, existing only to prove one parity claim.

`docs/parity.md` carried "Custom tool definitions" as unreachable, on the
grounds that the CLI "can switch its own built-in tools on and off but cannot
define one with your schema". That is true of `--tools`. It is not true of the
CLI, which speaks MCP: a server registered with `--mcp-config` contributes tools
whose names, descriptions and JSON input schemas are entirely the caller's.

So this file defines one tool the model cannot answer without calling, because
its return value is not derivable from its arguments -- a keyed digest over a
secret this process holds and the model never sees. If the answer comes back
right, the schema reached the model, the model chose the tool, the arguments
validated, and the result came back. Nothing weaker would prove it.

JSON-RPC 2.0 over newline-delimited stdio. Standard library only, per house
rules.
"""

from __future__ import annotations

import hashlib
import json
import sys

PROTOCOL_VERSION = "2024-11-05"

# Not derivable from the arguments, so a correct answer cannot be a lucky guess.
SECRET = "e7b1c4"

TOOLS = [
    {
        "name": "keyed_digest",
        "description": (
            "Compute the repository's keyed digest for a phrase. There is no way "
            "to derive this without calling the tool; do not guess it."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "phrase": {"type": "string", "description": "The phrase to digest."},
                "length": {
                    "type": "integer",
                    "description": "Hex characters to return, 4 to 32.",
                    "minimum": 4,
                    "maximum": 32,
                    "default": 8,
                },
            },
            "required": ["phrase"],
            "additionalProperties": False,
        },
    }
]


def keyed_digest(phrase: str, length: int = 8) -> str:
    length = max(4, min(32, int(length)))
    return hashlib.sha256((SECRET + phrase).encode()).hexdigest()[:length]


def handle(request: dict) -> dict | None:
    method = request.get("method")
    rid = request.get("id")

    if method == "initialize":
        return {
            "jsonrpc": "2.0", "id": rid,
            "result": {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "parity-probe", "version": "1.0.0"},
            },
        }

    if method in ("notifications/initialized", "initialized"):
        return None  # a notification carries no id and takes no reply

    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": rid, "result": {"tools": TOOLS}}

    if method == "tools/call":
        params = request.get("params") or {}
        name = params.get("name")
        args = params.get("arguments") or {}
        if name != "keyed_digest":
            return {"jsonrpc": "2.0", "id": rid,
                    "error": {"code": -32602, "message": f"no such tool: {name}"}}
        if "phrase" not in args:
            return {"jsonrpc": "2.0", "id": rid,
                    "error": {"code": -32602, "message": "phrase is required"}}
        value = keyed_digest(args["phrase"], args.get("length", 8))
        return {"jsonrpc": "2.0", "id": rid,
                "result": {"content": [{"type": "text", "text": value}],
                           "isError": False}}

    if rid is None:
        return None
    return {"jsonrpc": "2.0", "id": rid,
            "error": {"code": -32601, "message": f"method not found: {method}"}}


def main() -> int:
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            request = json.loads(line)
        except json.JSONDecodeError:
            continue
        response = handle(request)
        if response is not None:
            sys.stdout.write(json.dumps(response) + "\n")
            sys.stdout.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
