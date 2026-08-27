"""Claude-backed answer generation.

Optional. The core pipeline runs without it (see `generate/extractive.py`), and
the official `anthropic` SDK is imported lazily so a missing package degrades to
the extractive path instead of breaking the import graph. Install with:

    pip install "oodarag[llm]"

Two choices worth explaining:

**Prompt caching on the system prompt.** The instructions and the citation
contract are byte-identical on every request; the retrieved evidence and the
question are not. Caching is a prefix match, so the stable half goes in `system`
with a cache breakpoint and the volatile half goes in `messages` after it. Get
that order wrong and the cache never hits.

**Adaptive thinking.** Deciding which of eight retrieved passages actually
answers a question - and refusing when none of them do - is exactly the kind of
judgement that benefits from reasoning before answering.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from oodarag.util.logging import get_logger

log = get_logger("generate.claude")

DEFAULT_MODEL = "claude-opus-5"

SYSTEM_PROMPT = """You answer questions strictly from the numbered evidence you are given.

Rules:
1. Every factual claim must end with a citation marker: [1], [2], and so on, \
matching the numbered evidence. A sentence with a claim and no marker is a failure.
2. Cite only markers that appear in the evidence. Never invent a number.
3. If the evidence does not answer the question, say exactly what is missing. \
Do not fill the gap from your own knowledge - an honest "the retrieved sources \
do not cover X" is the correct answer, and a fluent guess is not.
4. When sources disagree, say so and cite both.
5. Be direct. Lead with the answer, then the supporting detail. No preamble, \
no restating the question, no summary of what you are about to say.
6. Quote exact identifiers - function names, flags, error strings, versions - \
verbatim from the evidence rather than paraphrasing them."""


@dataclass
class ClaudeGenerator:
    """Generate a grounded answer with Claude."""

    model: str = DEFAULT_MODEL
    max_tokens: int = 4096
    effort: str = "medium"
    system_prompt: str = SYSTEM_PROMPT
    name: str = "claude"
    _client: Any = field(default=None, init=False, repr=False)

    @property
    def available(self) -> bool:
        try:
            self._ensure_client()
        except Exception as e:
            log.debug("claude generator unavailable", err=str(e)[:160])
            return False
        return True

    def _ensure_client(self) -> Any:
        if self._client is None:
            import anthropic  # lazy: optional dependency

            # A bare constructor resolves ANTHROPIC_API_KEY, ANTHROPIC_AUTH_TOKEN
            # or an `ant auth login` profile, in that order.
            self._client = anthropic.Anthropic()
        return self._client

    def generate(self, question: str, context: str) -> str:
        client = self._ensure_client()
        user_content = (
            f"Evidence:\n\n{context}\n\n"
            f"---\n\nQuestion: {question}\n\n"
            "Answer using only the evidence above, with a citation marker on every claim."
        )
        response = client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            # Stable prefix, cached: instructions never vary between requests.
            system=[{
                "type": "text",
                "text": self.system_prompt,
                "cache_control": {"type": "ephemeral"},
            }],
            messages=[{"role": "user", "content": user_content}],
            thinking={"type": "adaptive"},
            output_config={"effort": self.effort},
        )
        # A safety decline is a valid outcome, not an exception: surface it
        # rather than reading .content and getting an empty answer.
        if getattr(response, "stop_reason", None) == "refusal":
            details = getattr(response, "stop_details", None)
            category = getattr(details, "category", None) if details else None
            log.warn("generation refused", category=str(category))
            return f"(The model declined to answer this request. Category: {category}.)"

        usage = getattr(response, "usage", None)
        if usage is not None:
            log.debug("claude usage",
                      input=getattr(usage, "input_tokens", 0),
                      output=getattr(usage, "output_tokens", 0),
                      cache_read=getattr(usage, "cache_read_input_tokens", 0))
        return "".join(block.text for block in response.content if block.type == "text").strip()
