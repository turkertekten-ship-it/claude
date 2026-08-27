"""Are the URLs this repository publishes well-formed and pointing at itself?

Reachability is deliberately not the headline. Whether a host answers today is a
fact about the network, not about the repository, and a checker that reports
`LINK_DEAD` from inside an egress-filtered container has told the reader
something false about their documentation. So with `allow_network` off - the
default - this emits exactly one aggregate `UNVERIFIABLE` finding saying how
many URLs it found and that it did not try them. One line, not one per link:
a hundred identical "not checked" entries is how a report teaches its reader to
skim past the section that matters.

What it *can* decide offline is the class of URL error that survives review
precisely because it looks fine: a scheme typo, a placeholder host that shipped,
and - the one worth having - a `github.com/owner/repo` link that names a
different repository from this one's own origin. That last one is a copy-paste
artifact. It is invisible in rendered markdown, it resolves, it returns 200, and
it points users and user-agent strings at somebody else's project.
"""

from __future__ import annotations

import re
import urllib.error
import urllib.parse
import urllib.request
from collections import defaultdict
from dataclasses import dataclass
from typing import Iterator

from tools.checkers.paths import _own_slug
from tools.claims import RepoIndex
from tools.evidence import Claim, Evidence, Finding, Severity, Verdict
from tools.registry import CheckConfig, register

#: A URL, stopping before the punctuation that ends the sentence around it.
#: Trailing `.,;:!?` and a closing bracket are trimmed, since markdown wraps
#: links in `()` and prose ends them with a full stop.
#:
#: The near-miss schemes are matched deliberately. A pattern that only accepts
#: `https?://` cannot ever report a scheme typo, because the typo is exactly
#: what stops the pattern matching - the malformed-URL rule would be dead code
#: dressed as a check. `ftp://`, `git://` and `mailto:` are *not* matched: those
#: are correct URLs of other kinds, and flagging them would be this checker
#: inventing a rule nobody asked for.
_URL_RE = re.compile(
    r"\b(?:https?|htp|htps|hxxp|ttp|htt|hhtp)://[^\s<>\"'`\\]+"
    r"|\bhttps?:/(?!/)[^\s<>\"'`\\]+",
    re.IGNORECASE,
)
#: The schemes that are actually correct. Anything else `_URL_RE` admitted is a
#: typo by construction.
_GOOD_SCHEMES = frozenset({"http", "https"})
#: Hosts that mean "fill this in later".
_PLACEHOLDER_HOSTS = frozenset({
    "example.com", "example.org", "example.net", "www.example.com",
    "localhost", "127.0.0.1", "0.0.0.0", "your-org.com", "yourname.com",
    "changeme.com", "todo.com", "foo.com", "bar.com",
})
#: Placeholder path segments left in a copied template.
_PLACEHOLDER_SEGMENTS = frozenset({
    "your-org", "yourname", "your_org", "changeme", "todo", "fixme",
    "owner", "username", "my-org", "org-name", "repo-name",
})
_TRAILING = ".,;:!?)]}>'\""
_GITHUB_HOSTS = frozenset({"github.com", "www.github.com", "raw.githubusercontent.com"})

#: A file whose string literals are fixtures rather than published links. A
#: test for this very checker has to contain a deliberately wrong URL in order
#: to assert that it is caught; reading that fixture as a claim turns every
#: passing test into a finding, and the checker ends up loudest about the code
#: that proves it works.
_FIXTURE_RE = re.compile(r"(?:^|/)tests?/|(?:^|/)(?:test_[^/]+|[^/]+_test)\.py$")

#: A URL carrying a substitution hole is a template, not a destination.
#: `f"https://github.com/{self.slug}/blob/{sha}/{path}"` is code that builds a
#: link at runtime; the host it will eventually name is not knowable here.
_TEMPLATE_RE = re.compile(r"[{}<>]|%s|%\(|\$\{|\$[A-Za-z_]")


def _clean(url: str) -> str:
    while url and url[-1] in _TRAILING:
        url = url[:-1]
    return url


def _github_slug(url: str) -> str:
    parts = urllib.parse.urlsplit(url)
    if parts.hostname not in _GITHUB_HOSTS:
        return ""
    segments = [s for s in parts.path.split("/") if s]
    if len(segments) < 2:
        return ""
    return f"{segments[0]}/{segments[1].removesuffix('.git')}"


def _urls(repo: RepoIndex) -> list[tuple[Claim, str]]:
    """Every URL in the tree, paired with the line that carries it."""
    out: list[tuple[Claim, str]] = []
    for source in repo.files:
        if _FIXTURE_RE.search(source.rel):
            continue
        for lineno, raw in enumerate(source.lines, start=1):
            for match in _URL_RE.finditer(raw):
                url = _clean(match.group(0))
                if not url or _TEMPLATE_RE.search(url):
                    continue
                # A bare scheme with nothing after it is prose naming a scheme
                # ("correct it to https://"), not a link that resolves anywhere.
                if url.rstrip(":/").lower() in ("http", "https"):
                    continue
                out.append((Claim(raw.strip()[:300], source.rel, lineno, kind="url"), url))
    return out


@dataclass
class LinksChecker:
    name: str = "links"
    description: str = "Published URLs are well-formed, not placeholders, and name this repo."

    def check(self, repo: RepoIndex, config: CheckConfig) -> Iterator[Finding]:
        found = _urls(repo)
        if not found:
            return
        own = _own_slug(repo)

        for claim, url in found:
            yield from self._offline(claim, url, own)

        distinct = sorted({url for _, url in found})
        if not config.allow_network:
            yield Finding(
                checker=self.name, code="LINK_REACHABILITY_UNCHECKED",
                verdict=Verdict.UNVERIFIABLE, severity=Severity.INFO,
                claim=found[0][0],
                detail=(f"{len(distinct)} distinct URL(s) were found and none was requested: "
                        "the network is disabled, and a host that does not answer from inside "
                        "this sandbox is not evidence that a link is broken. Re-run with "
                        "--network to check reachability."),
            )
            return

        for url in distinct:
            claim = next(c for c, u in found if u == url)
            yield from self._reach(claim, url)

    # ------------------------------------------------------------------ offline

    def _offline(self, claim: Claim, url: str, own: str) -> Iterator[Finding]:
        here = Evidence.at(claim.path, claim.line, claim.text,
                           summary=f"{claim.path}:{claim.line} publishes {url}")
        scheme = url.split(":", 1)[0].lower()
        if scheme not in _GOOD_SCHEMES or not url[len(scheme):].startswith("://"):
            yield Finding(
                checker=self.name, code="LINK_MALFORMED",
                verdict=Verdict.CONTRADICTED, severity=Severity.ERROR, claim=claim,
                evidence=[here],
                detail=f"{url!r} has a malformed scheme: {scheme!r} followed by "
                       f"{url[len(scheme):len(scheme) + 3]!r}.",
                remedy="Correct the scheme to http:// or https://.")
            return
        parts = urllib.parse.urlsplit(url)
        if not parts.hostname or "." not in parts.hostname:
            yield Finding(
                checker=self.name, code="LINK_MALFORMED",
                verdict=Verdict.CONTRADICTED, severity=Severity.ERROR, claim=claim,
                evidence=[here], detail=f"{url!r} has no resolvable host.",
                remedy="Correct the URL.")
            return

        host = parts.hostname.lower()
        segments = {s.lower() for s in parts.path.split("/") if s}
        if host in _PLACEHOLDER_HOSTS or (segments & _PLACEHOLDER_SEGMENTS):
            # A line that is openly demonstrating a shape is not a mistake. The
            # cue has to be looked for in the prose *around* the URL, with the
            # URL removed first: `example.com` contains the word "example", so
            # searching the whole line suppresses every finding this rule exists
            # to make.
            surrounding = claim.text.lower().replace(url.lower(), " ")
            if re.search(r"\b(?:e\.g\.|for example|such as|placeholder|like this)\b", surrounding):
                return
            yield Finding(
                checker=self.name, code="LINK_PLACEHOLDER",
                verdict=Verdict.UNSUPPORTED, severity=Severity.WARN, claim=claim,
                evidence=[here],
                detail=f"{url!r} still contains a template placeholder.",
                remedy="Replace it with the real destination.")
            return

        slug = _github_slug(url)
        if own and slug and slug != own:
            yield Finding(
                checker=self.name, code="LINK_WRONG_REPO",
                verdict=Verdict.CONTRADICTED, severity=Severity.WARN, claim=claim,
                evidence=[here, Evidence.measured(
                    f"git origin names {own!r}, this URL names {slug!r}",
                    value=own, path=".git/config")],
                detail=(f"{url!r} points at {slug!r}, but this repository's origin remote is "
                        f"{own!r}. A link that resolves to the wrong project is invisible in "
                        "rendered markdown."),
                remedy=f"Point it at {own}, or say why another repository is meant.")

    # ------------------------------------------------------------------ network

    def _reach(self, claim: Claim, url: str) -> Iterator[Finding]:
        request = urllib.request.Request(url, method="HEAD",
                                         headers={"User-Agent": "ultrareview/1.0"})
        try:
            with urllib.request.urlopen(request, timeout=10) as resp:
                status = resp.status
        except urllib.error.HTTPError as e:
            if e.code in (403, 405, 501):  # HEAD refused; the URL may still be fine
                yield Finding(
                    checker=self.name, code="LINK_METHOD_REFUSED",
                    verdict=Verdict.UNVERIFIABLE, severity=Severity.INFO, claim=claim,
                    detail=f"{url!r} refused HEAD with {e.code}; reachability is undetermined.")
                return
            yield Finding(
                checker=self.name, code="LINK_DEAD",
                verdict=Verdict.CONTRADICTED, severity=Severity.WARN, claim=claim,
                evidence=[Evidence.at(claim.path, claim.line, claim.text),
                          Evidence.measured(f"HTTP {e.code} for {url}", value=e.code, path=url)],
                detail=f"{url!r} returned HTTP {e.code}.",
                remedy="Update or remove the link.")
            return
        except Exception as e:
            # A transport failure is a fact about this sandbox, not the link.
            yield Finding(
                checker=self.name, code="LINK_UNREACHABLE",
                verdict=Verdict.UNVERIFIABLE, severity=Severity.INFO, claim=claim,
                detail=(f"{url!r} could not be reached from here "
                        f"({type(e).__name__}); that is not evidence the link is broken."))
            return
        if status >= 400:
            yield Finding(
                checker=self.name, code="LINK_DEAD",
                verdict=Verdict.CONTRADICTED, severity=Severity.WARN, claim=claim,
                evidence=[Evidence.at(claim.path, claim.line, claim.text),
                          Evidence.measured(f"HTTP {status} for {url}", value=status, path=url)],
                detail=f"{url!r} returned HTTP {status}.",
                remedy="Update or remove the link.")


register(LinksChecker())
