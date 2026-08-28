"""Grounded answering: extract, then verify.

Nothing here generates text. The answerer copies sentences out of retrieved
chunks; the verifier checks each quote against the chunk it claims. An answer
that survives both is one whose every clause can be pointed at in a source.
"""

from oodarag.answer.extractive import ExtractiveAnswerer
from oodarag.answer.verify import coverage, normalise, quote_supported, verify_citations

__all__ = ["ExtractiveAnswerer", "coverage", "normalise", "quote_supported",
           "verify_citations"]
