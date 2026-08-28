"""Stable hashing helpers.

Ids must be deterministic across processes and machines: the incremental
ingest path decides "new vs changed vs unchanged" purely by comparing hashes,
and the embedding cache is keyed by content hash. Python's builtin `hash()` is
salted per process, so it is never used here.

The parts of a composite key are framed, not merely joined. Concatenation makes
("ab", "c") and ("a", "bc") the same key, which is how a document quietly
inherits another document's id; a separator alone only moves the problem to
inputs that contain the separator, and document text is exactly the kind of
input that eventually contains anything. Each part is therefore length-prefixed,
so the encoding is unambiguous whatever the parts hold.
"""

from __future__ import annotations

import hashlib


def sha256_hex(*parts: str) -> str:
    h = hashlib.sha256()
    for p in parts:
        # surrogatepass, not replace: paths and API payloads that were decoded
        # with surrogateescape carry lone surrogates, and "replace" would map
        # every one of them to "?" - turning distinct ids into one id.
        raw = p.encode("utf-8", "surrogatepass")
        h.update(f"{len(raw)}\x1f".encode("ascii"))  # unit separator, unambiguous framing
        h.update(raw)
    return h.hexdigest()


def content_hash(*parts: str) -> str:
    """Short content fingerprint. 16 hex chars = 64 bits, ample for change detection."""
    return sha256_hex(*parts)[:16]


def stable_id(*parts: str) -> str:
    """A readable, collision-resistant id for documents and chunks."""
    return sha256_hex(*parts)[:24]


def blake_bucket(token: str, buckets: int, salt: str = "") -> int:
    """Map a token into [0, buckets) deterministically (the hashing trick).

    A non-positive `buckets` is a misconfigured feature dimension arriving from
    config; it collapses to bucket 0 rather than raising ZeroDivisionError (or,
    for a negative modulus, quietly returning an index outside the range the
    signature promises).
    """
    if buckets < 1:
        return 0
    digest = hashlib.blake2b((salt + token).encode("utf-8", "surrogatepass"), digest_size=8)
    return int.from_bytes(digest.digest(), "big") % buckets


def blake_sign(token: str, salt: str = "s") -> int:
    """Deterministic +1/-1 sign, so hash collisions cancel instead of accumulating."""
    digest = hashlib.blake2b((salt + token).encode("utf-8", "surrogatepass"), digest_size=2)
    return 1 if digest.digest()[0] & 1 else -1
