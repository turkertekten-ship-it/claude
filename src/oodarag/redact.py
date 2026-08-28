"""Scrub identifiers at the connector boundary, before anything is stored.

This module is what makes the pipeline safe to point at a regulated firm's real
documents. Redaction happens at ingest rather than at display, because anything
written to the index is written to disk, and a leak that reaches disk has
already happened by the time a renderer decides to hide it.

**The trap this is built around is over-matching, not under-matching.** A
Turkish national ID is eleven digits. So is a lira amount above ten million
written without separators, a timestamp, and half the reference numbers in a
KAP filing. A rule that fires on every eleven-digit run does not protect a
document, it destroys it — and it destroys it silently, which is worse, because
the corrupted text still reads as plausible Turkish and still indexes cleanly.

So every numeric identifier here is **checksum-validated** before it is
redacted: TCKN by its own digit algorithm, VKN by its, IBAN by ISO 7064 mod-97,
cards by Luhn. A candidate that fails its checksum is left alone. Tests assert
that amounts, dates and ISINs survive a pass unchanged.

Placeholders are stable and typed — ``[REDACTED:TCKN:a1b2]`` — where the suffix
is a short keyed hash of the original. The same person redacts to the same token
across every document, so the corpus stays joinable, while the plaintext is
never stored. The key is per-process by default: a persistent one would make the
tokens a rainbow-table target across a corpus this small.
"""

from __future__ import annotations

import hmac
import os
import re
import secrets
from collections.abc import Callable
from dataclasses import dataclass
from typing import Literal

from oodarag.util.text import redact_secrets

Kind = Literal["TCKN", "VKN", "IBAN", "CARD", "EMAIL", "PHONE", "SECRET"]


@dataclass(slots=True, frozen=True)
class Finding:
    kind: Kind
    start: int
    end: int
    sample: str
    confidence: float

    @property
    def length(self) -> int:
        return self.end - self.start


# --------------------------------------------------------------------------
# Checksums. Each returns False for anything it is not sure about.
# --------------------------------------------------------------------------

def valid_tckn(value: str) -> bool:
    """Turkish national identification number.

    Eleven digits, first non-zero, with two check digits::

        d10 = ((d1+d3+d5+d7+d9) * 7 - (d2+d4+d6+d8)) mod 10
        d11 = (d1 + ... + d10) mod 10

    The algorithm accepts roughly one in a hundred random eleven-digit strings,
    which is what makes it usable as a filter: without it, every large lira
    figure in a document would be redacted.
    """
    if len(value) != 11 or not value.isdigit() or value[0] == "0":
        return False
    d = [int(c) for c in value]
    odd = d[0] + d[2] + d[4] + d[6] + d[8]
    even = d[1] + d[3] + d[5] + d[7]
    if (odd * 7 - even) % 10 != d[9]:
        return False
    return sum(d[:10]) % 10 == d[10]


def valid_vkn(value: str) -> bool:
    """Turkish tax number (vergi kimlik numarası), ten digits with a check digit."""
    if len(value) != 10 or not value.isdigit():
        return False
    d = [int(c) for c in value]
    total = 0
    for i in range(9):
        tmp = (d[i] + 10 - (i + 1)) % 10
        if tmp == 0:
            total += tmp
        else:
            p = (tmp * pow(2, 10 - (i + 1))) % 9
            total += 9 if p == 0 else p
    return d[9] == (10 - (total % 10)) % 10


def valid_iban(value: str) -> bool:
    """ISO 7064 mod-97. Turkish IBANs are 26 characters."""
    s = re.sub(r"[\s-]", "", value).upper()
    if len(s) < 15 or len(s) > 34 or not s[:2].isalpha() or not s[2:4].isdigit():
        return False
    if s.startswith("TR") and len(s) != 26:
        return False
    rearranged = s[4:] + s[:4]
    digits = "".join(str(ord(c) - 55) if c.isalpha() else c for c in rearranged)
    if not digits.isdigit():
        return False
    return int(digits) % 97 == 1


def valid_luhn(value: str) -> bool:
    digits = [int(c) for c in re.sub(r"[\s-]", "", value) if c.isdigit()]
    if len(digits) < 13 or len(digits) > 19:
        return False
    total, parity = 0, len(digits) % 2
    for i, d in enumerate(digits):
        if i % 2 == parity:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return total % 10 == 0


# --------------------------------------------------------------------------
# Candidate patterns. Deliberately loose — the checksum is the real filter.
# --------------------------------------------------------------------------

_PATTERNS: tuple[tuple[Kind, re.Pattern[str], Callable[[str], bool] | None, float], ...] = (
    ("IBAN", re.compile(r"\bTR[\s-]?\d{2}(?:[\s-]?\d{4}){5}[\s-]?\d{2}\b"), valid_iban, 0.99),
    ("EMAIL", re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b"), None, 0.95),
    # +90 / 0 prefixed Turkish numbers, with or without separators.
    ("PHONE", re.compile(r"(?<![\w.])(?:\+90|0)[\s.-]?\(?5\d{2}\)?[\s.-]?\d{3}[\s.-]?\d{2}[\s.-]?\d{2}(?![\d-])"), None, 0.9),
    ("CARD", re.compile(r"(?<![\d.,])\d{4}[\s-]\d{4}[\s-]\d{4}[\s-]\d{4}(?![\d.,])"), valid_luhn, 0.95),
    # Bare 11 and 10 digit runs. The anchors distinguish a digit run that is
    # PART OF a formatted number from one merely followed by punctuation: a
    # separator counts only when a digit follows it, so 1.234.567,89 is excluded
    # while "TC 10100000046," is not. Getting this backwards either destroys
    # every amount in the document or leaks every identifier at the end of a
    # clause, and both failures are silent.
    ("TCKN", re.compile(r"(?<![\d.,/-])\d{11}(?![\d/-])(?![.,]\d)"), valid_tckn, 0.97),
    ("VKN", re.compile(r"(?<![\d.,/-])\d{10}(?![\d/-])(?![.,]\d)"), valid_vkn, 0.85),
)


class Redactor:
    """Finds and replaces identifiers, leaving the rest of the document intact."""

    def __init__(self, key: bytes | None = None, *, token_len: int = 4) -> None:
        # A per-process random key by default: stable within a run so a corpus
        # stays joinable, unguessable across runs so the tokens are not a
        # lookup table for a small population.
        env = os.environ.get("OODARAG_REDACT_KEY")
        self._key = key or (env.encode() if env else secrets.token_bytes(32))
        self._token_len = max(2, min(16, token_len))

    def token(self, kind: Kind, value: str) -> str:
        normalised = re.sub(r"[\s-]", "", value).upper()
        digest = hmac.new(self._key, f"{kind}:{normalised}".encode(), "sha256").hexdigest()
        return f"[REDACTED:{kind}:{digest[:self._token_len]}]"

    def scan(self, text: str) -> list[Finding]:
        """Every identifier found, ordered by position, without overlaps.

        Earlier patterns win an overlap. IBAN is first on purpose: a Turkish
        IBAN contains digit runs that would otherwise be offered to the VKN
        checker.
        """
        found: list[Finding] = []
        taken: list[tuple[int, int]] = []

        def overlaps(a: int, b: int) -> bool:
            return any(a < e and s < b for s, e in taken)

        for kind, pattern, checksum, confidence in _PATTERNS:
            for m in pattern.finditer(text):
                s, e = m.span()
                if overlaps(s, e):
                    continue
                raw = m.group(0)
                if checksum is not None and not checksum(raw):
                    continue  # the whole point: no checksum, no redaction
                taken.append((s, e))
                found.append(Finding(kind, s, e, raw, confidence))
        found.sort(key=lambda f: f.start)
        return found

    def redact(self, text: str) -> tuple[str, list[Finding]]:
        """Replace every validated identifier, then hand off to the secret scrubber.

        Returns the cleaned text and what was found. The findings carry offsets
        into the ORIGINAL text; the replacement changes lengths, so they are a
        record of what was removed rather than a map into the result.
        """
        if not text:
            return text, []
        findings = self.scan(text)
        out, cursor = [], 0
        for f in findings:
            out.append(text[cursor:f.start])
            out.append(self.token(f.kind, f.sample))
            cursor = f.end
        out.append(text[cursor:])
        cleaned = "".join(out)

        # API keys, tokens, private keys and connection strings. Reused rather
        # than reimplemented so there is one definition of "secret" in the
        # codebase.
        scrubbed = redact_secrets(cleaned)
        if scrubbed != cleaned:
            findings.append(Finding("SECRET", 0, 0, "<pattern>", 0.8))
        return scrubbed, findings

    def __call__(self, text: str) -> str:
        """Connector-boundary form: takes text, returns text."""
        return self.redact(text)[0]


#: A ready redactor for callers that do not need their own key.
default_redactor = Redactor()


def redact(text: str) -> tuple[str, list[Finding]]:
    return default_redactor.redact(text)


def scan(text: str) -> list[Finding]:
    return default_redactor.scan(text)
