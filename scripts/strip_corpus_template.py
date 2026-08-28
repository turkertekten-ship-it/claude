#!/usr/bin/env python3
"""Remove the site template from the external corpus, and record what was removed.

The corpus was 90.9% PyPI download-page furniture: file hashes, wheel names,
upload dates, Sigstore attestation blocks and full release histories.
`scrape/html.py` kept them correctly - they sit inside the page's main content
area, and no single-page extractor can tell them from the article. The signal is
cross-document repetition, which is what `scrape/boilerplate.py` measures.

This rewrites the corpus in place and updates the manifest so it describes the
files that are actually on disk. Provenance is unchanged: the source URL and the
fetch time still say where each page came from and when, and `raw_words` and
`raw_content_hash` preserve what was fetched, so the removal is auditable rather
than a silent edit.

    PYTHONPATH=src python3 scripts/strip_corpus_template.py [--dry-run]
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys

from oodarag.scrape.boilerplate import filter_corpus
from oodarag.util.hashing import content_hash

CORPUS = pathlib.Path("corpus/external/pypi")
MANIFEST = pathlib.Path("corpus/external/pypi-manifest.json")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true",
                        help="report what would change and write nothing")
    args = parser.parse_args()

    paths = sorted(CORPUS.glob("*.md"))
    if not paths:
        print(f"no documents under {CORPUS}", file=sys.stderr)
        return 1
    documents = {p.name: p.read_text(encoding="utf-8") for p in paths}
    filtered, report = filter_corpus(documents)

    if report.skipped_reason:
        print(f"nothing removed: {report.skipped_reason}", file=sys.stderr)
        return 1

    print(f"{report.documents} documents")
    print(f"template headings ({len(report.template_headings)}): "
          f"{', '.join(report.template_headings)}")
    print(f"{report.bytes_before} -> {report.bytes_after} bytes "
          f"({report.removed_share:.1%} removed)")

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    by_name = {entry["name"]: entry for entry in manifest["documents"]}
    for filename, text in sorted(filtered.items()):
        entry = by_name.get(filename[:-3])
        if entry is None:
            print(f"  ! {filename} is not in the manifest", file=sys.stderr)
            continue
        raw = documents[filename]
        # Recorded once. Re-running must not overwrite the original figures with
        # the already-filtered ones, which would erase the evidence of removal.
        entry.setdefault("raw_words", len(raw.split()))
        entry.setdefault("raw_content_hash", entry["content_hash"])
        entry["words"] = len(text.split())
        entry["content_hash"] = content_hash(text)

    manifest["_template_removal"] = {
        "why": ("PyPI project pages carry their download table, per-file hashes, "
                "attestations and release history inside the main content area, so "
                "a single-page extractor keeps them. They were 90.9% of this "
                "corpus, and IDF is computed over that text."),
        "how": ("scrape/boilerplate.py: a heading present in at least half the "
                "documents from one host is that host's template; its section is "
                "dropped down to the next heading of the same or a higher level."),
        "headings_removed": report.template_headings,
        "bytes_before": report.bytes_before,
        "bytes_after": report.bytes_after,
    }

    if args.dry_run:
        print("dry run: nothing written")
        return 0
    for filename, text in filtered.items():
        (CORPUS / filename).write_text(text, encoding="utf-8")
    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {len(filtered)} documents and updated {MANIFEST}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
