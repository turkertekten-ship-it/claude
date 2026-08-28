"""URL checks. The load-bearing case is what happens with the network off."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools.checkers.links import LinksChecker, _clean, _github_slug, _urls
from tools.claims import RepoIndex
from tools.registry import CheckConfig

ORIGIN = '[remote "origin"]\n\turl = https://github.com/acme/widget\n'


def repo(tmp: str, readme: str, *, origin: str | None = ORIGIN) -> Path:
    root = Path(tmp)
    if origin is not None:
        (root / ".git").mkdir(exist_ok=True)
        (root / ".git" / "config").write_text(origin)
    (root / "README.md").write_text(readme)
    return root


def run(root: Path, **kw):
    return list(LinksChecker().check(RepoIndex(root), CheckConfig(**kw)))


class TestExtraction(unittest.TestCase):
    def test_sentence_punctuation_is_not_part_of_the_url(self):
        self.assertEqual(_clean("https://a.com/x."), "https://a.com/x")
        self.assertEqual(_clean("https://a.com/x),"), "https://a.com/x")

    def test_a_balanced_closing_paren_belongs_to_the_url(self):
        # Regression: an unconditional trim truncated Wikipedia links, and with
        # --network the tool then requested an address in no file and reported
        # the resulting 404 against a link that was correct.
        wiki = "https://en.wikipedia.org/wiki/Fence_(architecture)"
        self.assertEqual(_clean(wiki), wiki)
        self.assertEqual(_clean(wiki + "."), wiki)

    def test_github_slug(self):
        self.assertEqual(_github_slug("https://github.com/acme/widget/blob/main/x.py"),
                         "acme/widget")
        self.assertEqual(_github_slug("https://github.com/acme/widget.git"), "acme/widget")
        self.assertEqual(_github_slug("https://pypi.org/project/x"), "")

    def test_urls_carry_their_line(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = repo(tmp, "# T\n\nSee https://github.com/acme/widget for more.\n")
            found = _urls(RepoIndex(root))
            self.assertEqual([(c.line, u) for c, u in found],
                             [(3, "https://github.com/acme/widget")])


class TestOfflineVerdicts(unittest.TestCase):
    def _codes(self, readme: str, **kw) -> list[str]:
        with tempfile.TemporaryDirectory() as tmp:
            return [f.code for f in run(repo(tmp, readme), **kw)]

    def test_reachability_is_one_aggregate_unverifiable_not_one_per_link(self):
        readme = ("# T\n\nhttps://github.com/acme/widget\n"
                  "https://docs.python.org/3/\nhttps://pypi.org/project/x\n")
        codes = self._codes(readme)
        self.assertEqual(codes.count("LINK_REACHABILITY_UNCHECKED"), 1)

    def test_the_aggregate_finding_is_not_a_problem(self):
        with tempfile.TemporaryDirectory() as tmp:
            findings = run(repo(tmp, "# T\n\nhttps://github.com/acme/widget\n"))
            self.assertTrue(all(not f.is_problem for f in findings))

    def test_a_malformed_scheme_is_an_error(self):
        self.assertIn("LINK_MALFORMED", self._codes("# T\n\nhtp://example.io/x\n"))

    def test_a_placeholder_host_is_a_warning(self):
        self.assertIn("LINK_PLACEHOLDER",
                      self._codes("# T\n\nSet the base to https://your-org.com/api\n"))

    def test_rfc2606_reserved_hosts_are_correct_usage_not_placeholders(self):
        # RFC 2606 reserves example.com/.org/.net *for* documentation, so using
        # one is following the standard. Flagging it made the checker fire on
        # every correctly-written docstring in the tree.
        for host in ("example.com", "example.org", "example.net"):
            with self.subTest(host=host):
                codes = self._codes(f"# T\n\nThe crawler reads https://{host}/robots.txt first.\n")
                self.assertNotIn("LINK_PLACEHOLDER", codes)

    def test_localhost_is_a_real_host_not_a_malformed_url(self):
        # Regression: a dotless hostname was reported CONTRADICTED/ERROR with
        # the detail "has no resolvable host", which is false, and it failed the
        # run for any README documenting a dev server.
        for url in ("http://localhost:8000/docs", "http://127.0.0.1:3000",
                    "http://buildserver/status"):
            with self.subTest(url=url):
                codes = self._codes(f"# T\n\nOpen {url} while developing.\n")
                self.assertNotIn("LINK_MALFORMED", codes)
                self.assertNotIn("LINK_PLACEHOLDER", codes)

    def test_an_ordinary_outbound_github_link_is_not_flagged(self):
        # Linking to a dependency, an upstream tool or a spec is the normal case
        # for an outbound link. The old rule fired on every one of them.
        for line in ("See https://github.com/python/cpython/issues/1 for background.",
                     "Built on https://github.com/someone-else/other.",
                     "Upstream: https://github.com/psf/requests"):
            with self.subTest(line=line):
                self.assertNotIn("LINK_WRONG_REPO", self._codes(f"# T\n\n{line}\n"))

    def test_a_self_identifying_link_to_the_wrong_repo_is_flagged(self):
        # The case worth keeping: a copied user-agent or clone command that
        # points readers and servers at somebody else's project.
        for line in ('UA = "tool/1.0 (+https://github.com/someone-else/other)"',
                     "git clone https://github.com/someone-else/other",
                     "repository = https://github.com/someone-else/other"):
            with self.subTest(line=line):
                self.assertIn("LINK_WRONG_REPO", self._codes(f"# T\n\n{line}\n"))

    def test_a_self_identifying_link_to_this_repo_is_not_flagged(self):
        line = "git clone https://github.com/acme/widget"
        self.assertNotIn("LINK_WRONG_REPO", self._codes(f"# T\n\n{line}\n"))

    def test_without_a_git_origin_the_repo_rule_is_silent(self):
        # Not knowing what "this repository" is called is a reason to say
        # nothing, not a reason to flag every GitHub link in the tree.
        with tempfile.TemporaryDirectory() as tmp:
            root = repo(tmp, "# T\n\ngit clone https://github.com/someone-else/other\n",
                        origin=None)
            self.assertNotIn("LINK_WRONG_REPO", [f.code for f in run(root)])

    def test_a_repo_with_no_urls_is_silent(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(run(repo(tmp, "# T\n\nNothing here.\n")), [])


if __name__ == "__main__":
    unittest.main()


class TestReachabilitySemantics(unittest.TestCase):
    """Only *gone* is a dead link.

    Everything else a server can say — it refused the method, it wants
    credentials, it is rate limiting, it is broken today — is a fact about the
    server at this moment. Reporting that as a broken link puts a false finding
    in front of a reader who then has to go and disprove it.
    """

    def setUp(self) -> None:
        self.checker = LinksChecker()
        self.calls: list[tuple[str, str]] = []

    def _with_responses(self, responses: dict[str, tuple[int | None, str]]):
        def probe(url: str, method: str):
            self.calls.append((method, url))
            return responses.get(method, (None, "URLError"))
        self.checker._probe = staticmethod(probe)  # type: ignore[method-assign]

    def _codes(self, responses):
        from tools.evidence import Claim
        self._with_responses(responses)
        claim = Claim("see https://h.test/x", "README.md", 3)
        return [f.code for f in self.checker._reach(claim, "https://h.test/x")]

    def test_a_200_is_silent(self):
        self.assertEqual(self._codes({"HEAD": (200, "")}), [])

    def test_head_falls_back_to_get(self):
        # api.github.com answers 400 to HEAD and 200 to GET. Without the
        # fallback the module docstring's promise was false and the link was
        # reported dead.
        self.assertEqual(self._codes({"HEAD": (400, "HTTP 400"), "GET": (200, "")}), [])
        self.assertEqual([m for m, _ in self.calls], ["HEAD", "GET"])

    def test_404_is_the_dead_link_case(self):
        codes = self._codes({"HEAD": (404, "HTTP 404"), "GET": (404, "HTTP 404")})
        self.assertEqual(codes, ["LINK_DEAD"])

    def test_410_is_also_gone(self):
        self.assertEqual(self._codes({"HEAD": (410, ""), "GET": (410, "")}), ["LINK_DEAD"])

    def test_a_refused_method_is_not_a_dead_link(self):
        for status in (400, 401, 403, 405, 429):
            with self.subTest(status=status):
                codes = self._codes({"HEAD": (status, ""), "GET": (status, "")})
                self.assertEqual(codes, ["LINK_NOT_CONFIRMED"])
                self.calls.clear()

    def test_a_server_error_is_not_a_dead_link(self):
        codes = self._codes({"HEAD": (503, ""), "GET": (503, "")})
        self.assertEqual(codes, ["LINK_NOT_CONFIRMED"])

    def test_a_transport_failure_is_unverifiable(self):
        codes = self._codes({})
        self.assertEqual(codes, ["LINK_UNREACHABLE"])

    def test_no_reachability_finding_is_ever_a_run_failure(self):
        from tools.evidence import Claim
        for responses in ({"HEAD": (404, "")}, {"HEAD": (503, "")}, {}):
            self._with_responses(responses)
            claim = Claim("x", "README.md", 1)
            for f in self.checker._reach(claim, "https://h.test/x"):
                self.assertNotEqual(f.severity.value, "error",
                                    "a network result must never fail the run")
