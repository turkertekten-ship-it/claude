"""HTML extraction quality.

These assert the properties that decide whether a scraped corpus is usable,
not the exact bytes of any one extraction: no script/style leakage, no
boilerplate, structure preserved, links absolute and complete.
"""

from __future__ import annotations

import unittest

from oodarag.scrape.html import extract
from tests.support.httpserver import page, prose


class BoilerplateRemovalTest(unittest.TestCase):
    def setUp(self):
        self.html = page("Chunking Strategies", prose(120, "chunk"),
                         links=["/a", "/b"], nofollow=["/spam"])
        self.page = extract(self.html, "https://docs.example.com/guide/chunking")

    def test_script_and_style_content_never_reaches_the_text(self):
        for leaked in ("SHOULD_NOT_APPEAR_IN_TEXT", "ALSO_SHOULD_NOT_APPEAR",
                       "CSS_SHOULD_NOT_APPEAR", "var tracking", "console.log"):
            self.assertNotIn(leaked, self.page.text, f"{leaked!r} leaked into extracted text")
            self.assertNotIn(leaked, self.page.markdown)

    def test_navigation_and_footer_are_stripped(self):
        for chrome in ("Accept all cookies", "All rights reserved", "Copyright 2026"):
            self.assertNotIn(chrome, self.page.text, f"boilerplate {chrome!r} survived")

    def test_main_content_survives(self):
        self.assertIn("Chunking Strategies", self.page.text)
        self.assertIn("retrieval", self.page.text)
        self.assertGreater(self.page.word_count, 100)

    def test_title_and_metadata_are_extracted(self):
        self.assertEqual(self.page.title, "Chunking Strategies")
        self.assertEqual(self.page.lang, "en")
        self.assertEqual(self.page.meta["description"], "Description of Chunking Strategies.")

    def test_links_are_absolute_and_include_chrome_links_for_crawling(self):
        urls = {link.url for link in self.page.links}
        self.assertIn("https://docs.example.com/a", urls)
        # Nav links are removed from the *text* but kept as crawl frontier.
        self.assertIn("https://docs.example.com/pricing", urls)
        self.assertTrue(all(u.startswith("https://") for u in urls))

    def test_nofollow_is_recorded(self):
        spam = [link for link in self.page.links if link.url.endswith("/spam")]
        self.assertEqual(len(spam), 1)
        self.assertTrue(spam[0].nofollow)


class StructurePreservationTest(unittest.TestCase):
    def test_code_fences_are_preserved_byte_for_byte(self):
        code = 'def f(x):\n    if x > 1:\n        return "deep"\n    return x'
        html = f"<html><body><main><h1>T</h1><pre><code>{code}</code></pre>"
        html += f"<p>{'word ' * 60}</p></main></body></html>"
        result = extract(html, "https://e.com/")
        self.assertIn("```", result.markdown)
        block = result.markdown.split("```")[1]
        self.assertIn('    if x > 1:', block, "indentation was collapsed")
        self.assertIn('        return "deep"', block, "nested indentation was collapsed")

    def test_heading_hierarchy_is_captured(self):
        html = ("<html><body><main><h1>Top</h1><p>a b c</p><h2>Middle</h2><p>d e f</p>"
                "<h3>Deep</h3><p>g h i</p></main></body></html>")
        result = extract(html, "https://e.com/", min_words=1)
        self.assertEqual(result.headings, [(1, "Top"), (2, "Middle"), (3, "Deep")])
        self.assertIn("## Middle", result.markdown)

    def test_lists_become_markdown_bullets(self):
        html = "<html><body><main><h1>L</h1><ul><li>alpha</li><li>beta</li></ul></main></body></html>"
        result = extract(html, "https://e.com/", min_words=1)
        self.assertIn("- alpha", result.markdown)
        self.assertIn("- beta", result.markdown)

    def test_inline_whitespace_is_not_swallowed(self):
        html = "<html><body><main><h1>W</h1><p>read <b>the</b> <i>docs</i> now</p></main></body></html>"
        result = extract(html, "https://e.com/", min_words=1)
        self.assertIn("read the docs now", result.text)


class MalformedHtmlTest(unittest.TestCase):
    def test_unclosed_tags_do_not_truncate_the_document(self):
        html = ("<html><body><main><h1>Broken</h1><p>first paragraph here"
                "<p>second paragraph here<div>third block here</main></body>")
        result = extract(html, "https://e.com/", min_words=1)
        for expected in ("first paragraph", "second paragraph", "third block"):
            self.assertIn(expected, result.text)

    def test_stray_closing_tag_does_not_unwind_the_stack(self):
        html = ("<html><body><main><h1>Stray</h1><p>before</p></div></span>"
                "<p>after the stray close</p></main></body></html>")
        result = extract(html, "https://e.com/", min_words=1)
        self.assertIn("before", result.text)
        self.assertIn("after the stray close", result.text,
                      "content after a stray closing tag was lost")

    def test_empty_document_yields_empty_page_not_an_exception(self):
        result = extract("", "https://e.com/")
        self.assertEqual(result.text, "")
        self.assertEqual(result.links, [])


class FallbackTest(unittest.TestCase):
    def test_content_wrapped_in_a_noise_class_is_still_extracted(self):
        # Aggressive pruning would drop this entirely; the conservative retry
        # must rescue it rather than returning an empty page.
        body = " ".join(["substantive"] * 80)
        html = f'<html><body><div class="sidebar"><h1>Rescued</h1><p>{body}</p></div></body></html>'
        result = extract(html, "https://e.com/")
        self.assertIn("substantive", result.text)
        self.assertGreater(result.word_count, 50)


class CanonicalTest(unittest.TestCase):
    def test_canonical_link_is_resolved_absolutely(self):
        html = page("V", prose(60), canonical="/project/requests/")
        result = extract(html, "https://pypi.org/project/requests/2.31.0/")
        self.assertEqual(result.canonical, "https://pypi.org/project/requests/")


if __name__ == "__main__":
    unittest.main()
