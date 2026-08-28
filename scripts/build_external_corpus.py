#!/usr/bin/env python3
"""Fetch the external evaluation corpus, reproducibly.

The corpus this project gates on was built once, by hand, and could not be
rebuilt - which is a poor property for the artifact every retrieval number is
measured against. This is the missing script.

It uses the pipeline's own parts rather than a separate scraper, so the corpus
is what `oodarag` would produce and a defect in extraction shows up here:
`util/http` for fetching, `scrape/robots` for the gate, `scrape/html` for
extraction, and `scrape/boilerplate` for the site template that a single-page
extractor cannot see (L26).

    PYTHONPATH=src python3 scripts/build_external_corpus.py --list packages.txt
    PYTHONPATH=src python3 scripts/build_external_corpus.py --add rich,attrs

Bounded on requests, bytes and wall clock, because everything network-facing
here is. A package that cannot be fetched is reported and skipped; the corpus
shrinks visibly rather than silently.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys
import time

from oodarag.scrape.boilerplate import filter_corpus
from oodarag.scrape.html import extract
from oodarag.scrape.robots import RobotsPolicy
from oodarag.util.hashing import content_hash
from oodarag.util.http import HttpClient, HttpError, TransportError

CORPUS = pathlib.Path("corpus/external/pypi")
MANIFEST = pathlib.Path("corpus/external/pypi-manifest.json")
USER_AGENT = "oodarag-corpus-builder (+https://github.com/turkertekten-ship-it/claude)"
PROJECT_URL = "https://pypi.org/project/{name}/"

#: PyPI's robots.txt disallows /pypi/*/json, so the JSON API is off limits and
#: the HTML project page is the only permitted source. That is not a detail to
#: rediscover: an unchecked JSON fetch would be both a robots violation and a
#: different document than the one the corpus claims to contain.
MIN_WORDS = 40


def fetch_one(client: HttpClient, robots: RobotsPolicy, name: str) -> tuple[str, str, str]:
    """Return (markdown, title, note). `note` is empty on success."""
    url = PROJECT_URL.format(name=name)
    if not robots.allows(url):
        return "", "", "refused by robots.txt"
    delay = robots.crawl_delay(url)
    if delay:
        time.sleep(min(delay, 5.0))
    try:
        response = client.get(url)
    except (HttpError, TransportError) as e:
        return "", "", f"fetch failed: {str(e)[:120]}"
    if response.status != 200:
        return "", "", f"HTTP {response.status}"
    body = response.body.decode("utf-8", "replace")
    page = extract(body, url=url)
    if page.blocked:
        # A 200 that is not a success. Named rather than counted as a short
        # page, because "blocked" and "genuinely thin" need different responses.
        return "", "", f"{page.blocked} (HTTP 200)"
    if len(page.text.split()) < MIN_WORDS:
        # A stub page indexed as a document is a document that answers nothing
        # and dilutes every term statistic. Better absent than empty.
        return "", "", f"only {len(page.text.split())} words after extraction"
    # `markdown`, not `text`. The template filter works on headings, and `text`
    # has none - so writing `text` made the filter a silent no-op and added 60
    # documents with every byte of their boilerplate. The per-page line below
    # reports what was *stored* for the same reason: reporting what was fetched
    # hid it completely.
    return page.markdown, (page.title or name), ""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--add", default="",
                        help="comma-separated package names to add")
    parser.add_argument("--list", type=pathlib.Path,
                        help="file of package names, one per line")
    parser.add_argument("--max-requests", type=int, default=200)
    parser.add_argument("--max-seconds", type=float, default=900.0)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    wanted: list[str] = [n.strip() for n in args.add.split(",") if n.strip()]
    if args.list:
        wanted += [line.strip() for line in args.list.read_text().splitlines()
                   if line.strip() and not line.startswith("#")]
    wanted = list(dict.fromkeys(wanted))
    if not wanted:
        print("nothing to do: pass --add or --list", file=sys.stderr)
        return 1

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    by_name = {entry["name"]: entry for entry in manifest["documents"]}
    have = set(by_name)
    todo = [n for n in wanted if n not in have]
    print(f"{len(wanted)} requested, {len(todo)} not already in the corpus")
    if not todo:
        return 0

    client = HttpClient(user_agent=USER_AGENT)
    robots = RobotsPolicy(client=client, user_agent=USER_AGENT)
    started = time.monotonic()
    fetched: dict[str, tuple[str, str]] = {}
    skipped: list[tuple[str, str]] = []

    for index, name in enumerate(todo):
        if index >= args.max_requests:
            skipped.append((name, "request budget spent"))
            continue
        if time.monotonic() - started > args.max_seconds:
            skipped.append((name, "wall-clock budget spent"))
            continue
        text, title, note = fetch_one(client, robots, name)
        if note:
            skipped.append((name, note))
            print(f"  - {name}: {note}")
            continue
        fetched[name] = (text, title)

    if not fetched:
        print("no documents fetched", file=sys.stderr)
        return 1


    # The template already removed from the corpus on disk. Without it the new
    # pages keep their boilerplate: relearning over 33 filtered pages and two
    # raw ones puts the raw pages' headings in 6% of documents, far under the
    # threshold, and the filter correctly concludes they are not a template.
    known = set(manifest.get("_template_removal", {}).get("headings_removed", []))
    existing = {p.stem: p.read_text(encoding="utf-8") for p in CORPUS.glob("*.md")}
    combined = dict(existing)
    combined.update({name: text for name, (text, _) in fetched.items()})
    filtered, report = filter_corpus(combined, known=known)
    print(f"\ntemplate: {len(report.template_headings)} headings, "
          f"{report.removed_share:.1%} of {report.documents} documents removed")

    # Fetched versus stored, per page. A page whose two numbers are equal was
    # not filtered - which is either a page with no template on it or a filter
    # that did nothing, and those must not look alike in the output.
    print(f"\n{'package':<22} {'fetched':>8} {'stored':>8}  removed")
    unfiltered = []
    for name in sorted(fetched):
        raw_words = len(fetched[name][0].split())
        kept_words = len(filtered[name].split())
        share = 1 - kept_words / max(1, raw_words)
        print(f"  {name:<20} {raw_words:>8} {kept_words:>8}  {share:>6.1%}")
        if kept_words == raw_words:
            unfiltered.append(name)
    if unfiltered:
        print(f"\n! {len(unfiltered)} page(s) had nothing removed: "
              f"{', '.join(unfiltered[:8])}")

    # The thinness check has to run on what will be stored, not on what was
    # fetched. Applied before filtering it passed pages that were 40 words of
    # prose and 17,000 words of download table, and they landed in the corpus as
    # eight-word documents that answer nothing and still carry a name a query
    # can match.
    too_thin = [name for name in fetched
                if len(filtered[name].split()) < MIN_WORDS]
    for name in too_thin:
        skipped.append((name, f"only {len(filtered[name].split())} words once the "
                              f"site template was removed"))
        del fetched[name]
    if not fetched:
        print("every fetched page was too thin to keep", file=sys.stderr)
        return 1

    if args.dry_run:
        print("dry run: nothing written")
        return 0

    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    for name, (raw, title) in fetched.items():
        text = filtered[name]
        (CORPUS / f"{name}.md").write_text(text, encoding="utf-8")
        manifest["documents"].append({
            "name": name,
            "url": PROJECT_URL.format(name=name),
            "title": title,
            "words": len(text.split()),
            "content_hash": content_hash(text),
            "fetched_at": now,
            "raw_words": len(raw.split()),
            "raw_content_hash": content_hash(raw),
        })
    # Rewriting existing pages too: the template is relearned over a corpus that
    # now includes the new pages, and a heading that only crosses the threshold
    # once they arrive must be removed everywhere or the corpus is inconsistent.
    for name, text in filtered.items():
        if name in existing and text != existing[name]:
            (CORPUS / f"{name}.md").write_text(text, encoding="utf-8")
            entry = by_name.get(name)
            if entry:
                entry["words"] = len(text.split())
                entry["content_hash"] = content_hash(text)
            print(f"  ~ {name}: rewritten under the relearned template")

    manifest["documents"].sort(key=lambda e: e["name"])
    manifest["_template_removal"]["headings_removed"] = report.template_headings
    manifest["_template_removal"]["bytes_before"] = report.bytes_before
    manifest["_template_removal"]["bytes_after"] = report.bytes_after
    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    print(f"\nadded {len(fetched)}, skipped {len(skipped)}, "
          f"corpus is now {len(manifest['documents'])} documents")
    for name, note in skipped:
        print(f"  skipped {name}: {note}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
