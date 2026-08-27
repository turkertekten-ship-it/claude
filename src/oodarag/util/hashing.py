"""Stable hashing helpers.

Ids must be deterministic across processes and machines: the incremental
ingest path decides "new vs changed vs unchanged" purely by comparing hashes,
and the embedding cache is keyed by content hash. Python's builtin `hash()` is
salted per process, so it is never used here.
"""

from __future__ import annotations

import hashlib


def sha256_hex(*parts: str) -> str:
    h = hashlib.sha256()
    for p in parts:
        h.update(p.encode("utf-8", "replace"))
        h.update(b"\x1f")  # unit separator, so ("ab","c") != ("a","bc")
    return h.hexdigest()


def content_hash(*parts: str) -> str:
    """Short content fingerprint. 16 hex chars = 64 bits, ample for change detection."""
    return sha256_hex(*parts)[:16]


def stable_id(*parts: str) -> str:
    """A readable, collision-resistant id for documents and chunks."""
    return sha256_hex(*parts)[:24]


def blake_bucket(token: str, buckets: int, salt: str = "") -> int:
    """Map a token into [0, buckets) deterministically (the hashing trick)."""
    digest = hashlib.blake2b((salt + token).encode("utf-8", "replace"), digest_size=8).digest()
    return int.from_bytes(digest, "big") % buckets


def blake_sign(token: str, salt: str = "s") -> int:
    """Deterministic +1/-1 sign, so hash collisions cancel instead of accumulating."""
    digest = hashlib.blake2b((salt + token).encode("utf-8", "replace"), digest_size=2).digest()
    return 1 if digest[0] & 1 else -1
