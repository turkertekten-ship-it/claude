"""Site-template removal, learned from a set of pages rather than declared.

`scrape/html.py` removes chrome it can identify from one page: navigation,
sidebars, cookie banners, anything whose markup says it is not the article. That
is everything a single-page extractor can know, and on some sites it is not
enough. A PyPI project page carries its download table, per-file hashes,
Sigstore attestations and full release history *inside the main content area*,
so a structural extractor keeps them - correctly, by its own lights.

Measured on the 33-page external corpus, that left **90.9% of the evaluation
corpus as boilerplate**: `coverage.md` was 252KB of which 1,962 bytes described
the project, and `cffi.md` 90KB of which 653. The damage is not merely wasted
space. IDF is computed over that text, so `file` - a word in every page's
"Download files", "File details" and "File hashes" - had an IDF of 0.08 and
carried no weight, while a corpus of hex digests and upload dates set the scale
that decides what counts as a rare term.

The signal a single page cannot see is repetition. A heading that appears in
most documents from one host is that host's template, whatever its markup says,
and a heading appearing 172 times *within* one document is not a section title.
Both are cheap to count and neither needs a model.

This runs over a set of documents, so it belongs to corpus construction rather
than to fetching. `scripts/build_external_corpus.py` is the caller.
"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field

_HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*#*$")

#: Below this many documents the statistic means nothing: with three pages, a
#: heading two of them happen to share looks exactly like a site template. The
#: filter reports that it did nothing rather than inventing a template.
MIN_DOCUMENTS = 5


@dataclass
class TemplateReport:
    """What the filter learned and what it removed, so a run is auditable."""

    documents: int = 0
    template_headings: list[str] = field(default_factory=list)
    bytes_before: int = 0
    bytes_after: int = 0
    skipped_reason: str = ""

    @property
    def removed_share(self) -> float:
        return 0.0 if not self.bytes_before else 1 - self.bytes_after / self.bytes_before


def _headings(text: str) -> list[tuple[int, str, int]]:
    """(level, normalized title, line index) for every markdown heading."""
    out = []
    for i, line in enumerate(text.splitlines()):
        m = _HEADING_RE.match(line)
        if m:
            out.append((len(m.group(1)), m.group(2).strip().lower(), i))
    return out


def learn_template(texts: list[str], *, min_share: float = 0.5) -> set[str]:
    """Headings that are this host's furniture rather than any page's content.

    One signal only: the heading appears in at least `min_share` of the
    documents. On the corpus this was written for the separation is wide - the
    eight template headings are in 67-100% of pages and the next-most-common
    heading, "Contributing", in 27%.

    A within-document repeat count was tried as a second, independent trigger,
    on the reasoning that no real section title appears 172 times in one page.
    It was removed: a changelog repeats "Fixed" 37 times and "Changed" 35, so
    the rule ate changelogs, and there is no threshold between 37 and 172 that
    is anything but a number fitted to this corpus. It also contradicted the
    premise - the signal a single page cannot see is repetition *across* pages,
    and a filter that claims to work on one page is claiming to see it.
    """
    if not texts or len(texts) < MIN_DOCUMENTS:
        return set()
    presence: Counter[str] = Counter()
    for text in texts:
        for title in {title for _, title, _ in _headings(text)}:
            presence[title] += 1
    threshold = min_share * len(texts)
    return {title for title, count in presence.items() if count >= threshold}


def strip_template(text: str, template: set[str]) -> str:
    """Drop each templated section: the heading and everything under it, up to
    the next heading of the same or a higher level.

    Nesting matters. Dropping `## Download files` has to take `### Source
    Distribution` with it, or the filter removes the label and leaves the table.
    """
    if not template:
        return text
    lines = text.splitlines()
    heads = _headings(text)
    drop = [False] * len(lines)
    for index, (level, title, line_no) in enumerate(heads):
        if title not in template:
            continue
        end = len(lines)
        for next_level, _, next_line in heads[index + 1:]:
            if next_level <= level:
                end = next_line
                break
        for i in range(line_no, end):
            drop[i] = True
    kept = [line for i, line in enumerate(lines) if not drop[i]]
    # Collapse the blank runs the removal leaves behind.
    out: list[str] = []
    for line in kept:
        if not line.strip() and out and not out[-1].strip():
            continue
        out.append(line)
    return "\n".join(out).strip() + "\n"


def filter_corpus(documents: dict[str, str], *,
                  min_share: float = 0.5) -> tuple[dict[str, str], TemplateReport]:
    """Strip the learned template from every document, and report what happened.

    Returns the documents unchanged, with a stated reason, when there are too
    few of them to learn anything - a filter that quietly does nothing is
    indistinguishable from one that is broken.
    """
    texts = list(documents.values())
    report = TemplateReport(documents=len(documents),
                            bytes_before=sum(len(t) for t in texts))
    if len(documents) < MIN_DOCUMENTS:
        report.bytes_after = report.bytes_before
        report.skipped_reason = (
            f"{len(documents)} documents is below the {MIN_DOCUMENTS} needed to "
            f"tell a site template from a coincidence")
        return dict(documents), report

    template = learn_template(texts, min_share=min_share)
    filtered = {name: strip_template(text, template) for name, text in documents.items()}
    report.template_headings = sorted(template)
    report.bytes_after = sum(len(t) for t in filtered.values())
    return filtered, report
