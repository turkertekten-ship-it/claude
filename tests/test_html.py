"""Tests for the HTML extractor: tolerance, boilerplate, links and metadata.

Nothing here touches the network or the filesystem - `extract` takes a string
and hands back a dataclass - so every fixture is inline HTML. The documents are
broken in the ways real pages are broken: unclosed tags, stray closing tags,
unquoted attributes, markup inside a script string, markup inside a comment, and
a tag truncated at EOF. The contract under test is that none of them raise, and
that none of them cost us the document: the recurring failure of a scraper is
not a crash, it is silently returning one paragraph of a ten paragraph article.
"""

from __future__ import annotations

import unittest
from unittest import mock

from oodarag.scrape import html as html_mod
from oodarag.scrape.html import MAX_TREE_DEPTH, ExtractedPage, Link, extract

# Long enough (>140 chars) to clear the candidate floor in `_find_main`, so that
# tests about boilerplate are not accidentally tests about the thin-page path.
PARA = (
    "Retrieval augmented generation only works when the text is clean, so this "
    "paragraph is deliberately long enough to be scored as real content by the "
    "extractor rather than skipped as an aside."
)


def paragraphs(count: int, tag: str = "p") -> str:
    return "".join(f"<{tag}>Paragraph {i}. {PARA}</{tag}>" for i in range(count))


def anchors(count: int, prefix: str = "/s") -> str:
    return "".join(
        f'<a href="{prefix}{i}">Section number {i} of the site</a> ' for i in range(count)
    )


# ------------------------------------------------------------------ tolerance


class ParserToleranceTestCase(unittest.TestCase):
    """Malformed markup must degrade, never explode and never truncate."""

    def test_stray_closing_tag_does_not_unwind_the_document(self) -> None:
        page = extract(f"<body><p>{PARA}</p></div></span></section><p>tail text</p></body>")
        self.assertIn("tail text", page.text)
        self.assertIn("Retrieval augmented", page.text)

    def test_unclosed_tags_keep_their_content(self) -> None:
        page = extract(f"<body><div><p>alpha {PARA}<div><p>beta text")
        self.assertIn("alpha", page.text)
        self.assertIn("beta text", page.text)

    def test_mismatched_inline_nesting(self) -> None:
        page = extract(f"<body><p><b>bold <i>both</b> italic</i> plain {PARA}</p></body>")
        for word in ("bold", "both", "italic", "plain"):
            self.assertIn(word, page.text)

    def test_unquoted_attributes_are_read(self) -> None:
        page = extract(
            f"<body><div class=site-nav>{anchors(3)}</div>"
            f"<div class=post-body>{paragraphs(2)}</div></body>",
            "https://example.com/",
        )
        self.assertIn("Paragraph 1", page.text)
        self.assertNotIn("Section number 1", page.text)

    def test_uppercase_tags_and_attributes(self) -> None:
        page = extract(f'<BODY><P CLASS=X>{PARA}</P><A HREF="/up">Up</A></BODY>', "https://e.com/")
        self.assertIn("Retrieval augmented", page.text)
        self.assertEqual([link.url for link in page.links], ["https://e.com/up"])

    def test_script_body_is_never_content(self) -> None:
        doc = (
            "<body><script>var s = '</div><p>injected</p>'; if (a < b) { x(); }</script>"
            f"<p>{PARA}</p></body>"
        )
        page = extract(doc)
        self.assertNotIn("injected", page.text)
        self.assertNotIn("var s", page.text)
        self.assertIn("Retrieval augmented", page.text)

    def test_style_and_noscript_are_never_content(self) -> None:
        doc = (
            "<body><style>.a{color:red}</style><noscript>please enable javascript</noscript>"
            f"<p>{PARA}</p></body>"
        )
        page = extract(doc)
        self.assertNotIn("color:red", page.text)
        self.assertNotIn("enable javascript", page.text)
        self.assertIn("Retrieval augmented", page.text)

    def test_comment_containing_markup_is_ignored(self) -> None:
        page = extract(f"<body><!-- <p>commented out</p> --><p>{PARA}</p></body>")
        self.assertNotIn("commented out", page.text)
        self.assertIn("Retrieval augmented", page.text)

    def test_unterminated_comment_at_eof(self) -> None:
        page = extract(f"<body><p>{PARA}</p><!-- dangling <p>markup</p>")
        self.assertIn("Retrieval augmented", page.text)
        self.assertNotIn("dangling", page.text)

    def test_unterminated_tag_at_eof(self) -> None:
        page = extract(f'<body><p>{PARA}</p><div class="teaser')
        self.assertIn("Retrieval augmented", page.text)
        self.assertNotIn("teaser", page.text)

    def test_cdata_section_is_not_emitted_as_text(self) -> None:
        page = extract(f"<body><![CDATA[ raw cdata ]]><p>{PARA}</p></body>")
        self.assertNotIn("raw cdata", page.text)
        self.assertIn("Retrieval augmented", page.text)

    def test_deep_nesting_does_not_blow_the_stack(self) -> None:
        depth = MAX_TREE_DEPTH * 30
        page = extract("<div>" * depth + f"<p>{PARA}</p>" + "</div>" * depth, "https://e.com/")
        self.assertIn("Retrieval augmented", page.text)

    def test_deep_nesting_of_unclosed_tags(self) -> None:
        page = extract("<div>" * 4000 + "deep content here")
        self.assertIn("deep content here", page.text)

    def test_degenerate_documents_return_an_empty_page(self) -> None:
        for doc in ("", "   ", "\n\n", "<p>", "</p>", "<<<>>>", "<!doctype html>"):
            with self.subTest(doc=doc):
                page = extract(doc, "https://e.com/")
                self.assertEqual(page.url, "https://e.com/")
                self.assertEqual(page.links, [])
                self.assertEqual(page.headings, [])
                self.assertIsInstance(page.text, str)

    def test_plain_text_document(self) -> None:
        page = extract("just some words, no markup at all")
        self.assertEqual(page.text, "just some words, no markup at all")


# ------------------------------------------------------------ text extraction


class TextExtractionTestCase(unittest.TestCase):
    def test_block_elements_are_separated(self) -> None:
        page = extract("<body><p>foo</p><p>bar</p><div>baz</div></body>")
        self.assertNotIn("foobar", page.text)
        self.assertNotIn("barbaz", page.text)
        self.assertEqual(page.text.split(), ["foo", "bar", "baz"])

    def test_br_is_a_newline(self) -> None:
        page = extract("<body><p>first line<br>second line</p></body>")
        self.assertIn("first line\nsecond line", page.text)

    def test_inline_elements_do_not_gain_whitespace(self) -> None:
        page = extract("<body><p>re<em>al</em>ly</p></body>")
        self.assertEqual(page.text, "really")

    def test_whitespace_between_inline_elements_survives(self) -> None:
        page = extract("<body><p><b>read the</b> <i>docs</i></p></body>")
        self.assertEqual(page.text, "read the docs")

    def test_entities_are_decoded_exactly_once(self) -> None:
        page = extract("<body><p>&lt;tag&gt; &amp; &amp;lt; &#8212; a&nbsp;b</p></body>")
        self.assertIn("<tag> & &lt; —", page.text)
        self.assertNotIn("&amp;", page.text)
        # NFKC folds the non-breaking space to a plain one; it stays a boundary.
        self.assertIn("a b", page.text)

    def test_entities_in_attributes_are_decoded_once(self) -> None:
        page = extract('<body><a href="/s?a=1&amp;b=2">q</a></body>', "https://e.com/")
        self.assertEqual([link.url for link in page.links], ["https://e.com/s?a=1&b=2"])

    def test_headings_are_marked_and_recorded(self) -> None:
        page = extract("<body><h1>Title Here</h1><h3>Sub Head</h3><p>body</p></body>")
        self.assertEqual(page.headings, [(1, "Title Here"), (3, "Sub Head")])
        self.assertIn("# Title Here", page.markdown)
        self.assertIn("### Sub Head", page.markdown)
        # The plain-text rendering keeps the words and drops the hashes.
        self.assertNotIn("#", page.text)
        self.assertIn("Title Here", page.text)

    def test_heading_spanning_a_block_stays_on_one_line(self) -> None:
        page = extract("<body><h2>Part <span>one</span><div>and two</div></h2></body>")
        self.assertEqual(page.headings, [(2, "Part one and two")])
        self.assertEqual(page.markdown, "## Part one and two")

    def test_empty_heading_is_dropped(self) -> None:
        page = extract("<body><h2>  </h2><p>text</p></body>")
        self.assertEqual(page.headings, [])

    def test_lists_render_with_markers_and_indentation(self) -> None:
        page = extract("<body><ul><li>one<ul><li>deep</li></ul></li><li>two</li></ul></body>")
        self.assertIn("- one", page.markdown)
        self.assertIn("  - deep", page.markdown)
        self.assertIn("- two", page.markdown)

    def test_ordered_list_marker(self) -> None:
        page = extract("<body><ol><li>first</li><li>second</li></ol></body>")
        self.assertIn("1. first", page.markdown)

    def test_unclosed_list_items_do_not_nest(self) -> None:
        page = extract("<body><ul><li>one<li>two</ul></body>")
        self.assertEqual([ln.strip() for ln in page.markdown.split("\n") if ln.strip()],
                         ["- one", "- two"])

    def test_unclosed_cells_stay_in_their_own_column(self) -> None:
        page = extract("<body><table><tr><td>cell a<td>cell b<tr><td>c<td>d</table></body>")
        self.assertIn("| cell a | cell b |", page.markdown)
        self.assertIn("| c | d |", page.markdown)

    def test_unclosed_anchor_does_not_swallow_the_next_link(self) -> None:
        doc = '<body><a href="/one">first<a href="/two">second</a></body>'
        page = extract(doc, "https://e.com/")
        self.assertEqual([(link.url, link.text) for link in page.links],
                         [("https://e.com/one", "first"), ("https://e.com/two", "second")])

    def test_unclosed_definition_list_items(self) -> None:
        page = extract("<body><dl><dt>term one<dd>meaning<dt>term two<dd>other</dl></body>")
        self.assertEqual(page.text.split("\n\n"), ["term one", "meaning", "term two", "other"])

    def test_table_rows_become_pipe_rows(self) -> None:
        doc = "<body><table><thead><tr><th>H1</th><th>H2</th></tr></thead>" \
              "<tbody><tr><td>a</td><td>b</td></tr></tbody></table></body>"
        page = extract(doc)
        self.assertIn("| H1 | H2 |", page.markdown)
        self.assertIn("| a | b |", page.markdown)

    def test_cells_outside_a_row_are_not_welded(self) -> None:
        page = extract("<body><table><td>x</td><td>y</td></table></body>")
        self.assertNotIn("xy", page.text)

    def test_cell_with_two_paragraphs_is_not_welded(self) -> None:
        page = extract("<body><table><tr><td><p>alpha</p><p>beta</p></td></tr></table></body>")
        self.assertIn("| alpha beta |", page.markdown)

    def test_blockquote_paragraphs_are_not_welded(self) -> None:
        page = extract("<body><blockquote><p>alpha</p><p>beta</p></blockquote></body>")
        self.assertNotIn("alphabeta", page.markdown)
        self.assertIn("> alpha", page.markdown)
        self.assertIn("> beta", page.markdown)

    def test_pre_preserves_whitespace_and_language(self) -> None:
        doc = ("<body><pre><code class=\"language-python\">def f(x):\n"
               "    return  x + 1\n</code></pre></body>")
        page = extract(doc)
        self.assertIn("```python\ndef f(x):\n    return  x + 1\n```", page.markdown)

    def test_pre_containing_a_fence_uses_a_longer_fence(self) -> None:
        page = extract("<body><pre>a\n```\nb</pre></body>")
        self.assertIn("````\na\n```\nb\n````", page.markdown)

    def test_image_alt_text_is_kept(self) -> None:
        page = extract('<body><p>see <img src="/a.png" alt="a chart"> here</p></body>')
        self.assertIn("[image: a chart]", page.text)

    def test_image_without_alt_is_a_word_boundary(self) -> None:
        page = extract('<body><p>see<img src="/a.png">here</p></body>')
        self.assertEqual(page.text, "see here")

    def test_horizontal_rule(self) -> None:
        page = extract("<body><p>a</p><hr><p>b</p></body>")
        self.assertIn("---", page.markdown)


# ---------------------------------------------------------------- whitespace


class TidyTestCase(unittest.TestCase):
    def test_runs_of_spaces_are_collapsed_in_prose(self) -> None:
        page = extract("<body><p>far      apart</p></body>")
        self.assertEqual(page.markdown, "far apart")

    def test_prose_mentioning_a_fence_still_gets_normalised(self) -> None:
        # A stray ``` in the text must not put the rest of the document into
        # "inside a code block" mode and leave it unnormalised.
        page = extract("<body><p>write ``` to fence</p><p>then      collapse</p></body>")
        self.assertIn("write ``` to fence", page.markdown)
        self.assertIn("then collapse", page.markdown)

    def test_code_fences_are_left_byte_for_byte(self) -> None:
        page = extract("<body><pre>def f():\n\n\n    return    1\n</pre></body>")
        self.assertIn("def f():\n\n\n    return    1", page.markdown)

    def test_blank_line_runs_are_collapsed_outside_fences(self) -> None:
        page = extract("<body><p>a</p>" + "<div></div>" * 5 + "<p>b</p></body>")
        self.assertEqual(page.markdown, "a\n\nb")


# ---------------------------------------------------------------- boilerplate


class BoilerplateTestCase(unittest.TestCase):
    def test_sibling_paragraphs_under_body_all_survive(self) -> None:
        # Regression: scoring picks one node, and with the paragraphs hanging
        # straight off <body> the winner used to be a single paragraph - the
        # extractor threw away four fifths of the article.
        page = extract(f"<html><body>{paragraphs(5)}</body></html>", "https://e.com/")
        for i in range(5):
            self.assertIn(f"Paragraph {i}.", page.text)

    def test_nav_and_footer_are_removed_when_there_is_content(self) -> None:
        doc = (
            f"<body><nav>{anchors(6)}</nav><div id=content>{paragraphs(3)}</div>"
            "<footer>Copyright 2026 Example Inc</footer></body>"
        )
        page = extract(doc, "https://e.com/")
        self.assertIn("Paragraph 2.", page.text)
        self.assertNotIn("Section number 2", page.text)
        self.assertNotIn("Copyright", page.text)

    def test_header_aside_and_menu_are_removed(self) -> None:
        doc = (
            f"<body><header>site header words</header><aside>aside words</aside>"
            f"<menu>menu words</menu><div id=content>{paragraphs(3)}</div></body>"
        )
        page = extract(doc, "https://e.com/")
        for noise in ("site header", "aside words", "menu words"):
            self.assertNotIn(noise, page.text)
        self.assertIn("Paragraph 2.", page.text)

    def test_a_page_that_is_all_navigation_is_not_emptied(self) -> None:
        page = extract(f"<body><nav>{anchors(12)}</nav></body>", "https://e.com/")
        self.assertIn("Section number 5", page.text)
        self.assertGreater(page.word_count, 20)

    def test_content_inside_a_noise_class_survives_via_fallback(self) -> None:
        page = extract(f'<body><div class="sidebar">{paragraphs(3)}</div></body>', "https://e.com/")
        self.assertIn("Paragraph 2.", page.text)

    def test_prose_with_a_footer_keeps_the_prose(self) -> None:
        doc = (f"<body><div id=wrap>{paragraphs(4)}</div>"
               '<footer><a href="/tos">Terms</a> Copyright</footer></body>')
        page = extract(doc, "https://e.com/")
        for i in range(4):
            self.assertIn(f"Paragraph {i}.", page.text)

    def test_widening_keeps_the_article_even_when_it_costs_a_nav(self) -> None:
        # The nav here has no semantic tag and no noise-ish class, so pruning
        # cannot see it. Keeping it is the acceptable failure; dropping three of
        # the four paragraphs is not.
        doc = f"<body><div class=topbar>{anchors(8)}</div>{paragraphs(4)}</body>"
        page = extract(doc, "https://e.com/")
        for i in range(4):
            self.assertIn(f"Paragraph {i}.", page.text)

    def test_head_text_is_never_dragged_into_the_body(self) -> None:
        # A CSS string containing `</style>` closes the element early - browsers
        # do the same - and leaves its tail loose in <head>. Widening the
        # selection must stop at <body> rather than adopt it.
        doc = ('<head><style>.a::after { content: "</style>"; }</head>'
               f"<body>{paragraphs(3)}</body>")
        page = extract(doc, "https://e.com/")
        self.assertTrue(page.text.startswith("Paragraph 0."), page.text[:40])
        self.assertIn("Paragraph 2.", page.text)

    def test_main_element_wins_over_everything_else(self) -> None:
        doc = f"<body><div class=topbar>{anchors(8)}</div><main>{paragraphs(3)}</main></body>"
        page = extract(doc, "https://e.com/")
        self.assertIn("Paragraph 2.", page.text)
        self.assertNotIn("Section number 2", page.text)

    def test_role_main_is_matched_per_token(self) -> None:
        doc = f'<body>{anchors(8)}<div role="main presentation">{paragraphs(3)}</div></body>'
        page = extract(doc, "https://e.com/")
        self.assertIn("Paragraph 2.", page.text)
        self.assertNotIn("Section number 2", page.text)

    def test_largest_article_element_wins(self) -> None:
        doc = f"<body><article>{paragraphs(1)}</article><article>{paragraphs(4)}</article></body>"
        page = extract(doc, "https://e.com/")
        self.assertIn("Paragraph 3.", page.text)
        self.assertEqual(page.text.count("Paragraph 0."), 1)

    def test_hidden_regions_are_dropped(self) -> None:
        doc = (
            "<body><div hidden>hidden words</div>"
            '<div aria-hidden="true">aria words</div>'
            '<div style="display: none">styled words</div>'
            f"<div id=content>{paragraphs(2)}</div></body>"
        )
        page = extract(doc, "https://e.com/")
        for noise in ("hidden words", "aria words", "styled words"):
            self.assertNotIn(noise, page.text)
        self.assertIn("Paragraph 1.", page.text)

    def test_hidden_false_is_not_hidden(self) -> None:
        page = extract(f'<body><div hidden="false"><p>{PARA}</p></div></body>')
        self.assertIn("Retrieval augmented", page.text)

    def test_chrome_roles_are_dropped_per_token(self) -> None:
        doc = (f'<body><div role="banner navigation">chrome words</div>'
               f"<div id=content>{paragraphs(2)}</div></body>")
        page = extract(doc, "https://e.com/")
        self.assertNotIn("chrome words", page.text)

    def test_conservative_mode_keeps_structural_boilerplate(self) -> None:
        doc = f"<body><footer>{paragraphs(2)}</footer></body>"
        self.assertIn("Paragraph 1.", extract(doc, "https://e.com/", aggressive=False).text)
        # Aggressively, the same document is empty - which is what makes the
        # thin-page retry in `extract` load-bearing rather than decorative.
        self.assertEqual(extract(doc, "https://e.com/", min_words=0).text, "")

    def test_min_words_governs_the_fallback(self) -> None:
        doc = f"<body><nav>{anchors(3)}</nav></body>"
        # Below the floor: retry without boilerplate removal rather than return
        # an empty page.
        self.assertIn("Section number 1", extract(doc, min_words=25).text)
        # With no floor at all the aggressive result stands, empty or not.
        self.assertEqual(extract(doc, min_words=0).text, "")

    def test_aggressive_result_is_kept_when_the_fallback_is_no_better(self) -> None:
        page = extract("<body><p>four short words here</p></body>", min_words=25)
        self.assertEqual(page.text, "four short words here")


# ---------------------------------------------------------------------- links


class LinkExtractionTestCase(unittest.TestCase):
    def test_relative_links_resolve_against_the_document_url(self) -> None:
        doc = ('<body><a href="/abs">a</a><a href="rel.html">b</a>'
               '<a href="../up.html">c</a><a href="//cdn.example.net/x">d</a></body>')
        page = extract(doc, "https://e.com/docs/guide/page.html")
        self.assertEqual(
            [link.url for link in page.links],
            [
                "https://e.com/abs",
                "https://e.com/docs/guide/rel.html",
                "https://e.com/docs/up.html",
                "https://cdn.example.net/x",
            ],
        )

    def test_base_href_overrides_the_document_url(self) -> None:
        doc = ('<html><head><base href="https://cdn.example.net/docs/"></head>'
               '<body><a href="guide.html">g</a></body></html>')
        page = extract(doc, "https://e.com/dir/page")
        self.assertEqual([link.url for link in page.links],
                         ["https://cdn.example.net/docs/guide.html"])

    def test_relative_base_href_resolves_against_the_document_url(self) -> None:
        doc = '<head><base href="/docs/"></head><body><a href="guide.html">g</a></body>'
        page = extract(doc, "https://e.com/dir/page")
        self.assertEqual([link.url for link in page.links], ["https://e.com/docs/guide.html"])

    def test_first_base_wins_and_a_non_http_base_is_ignored(self) -> None:
        doc = ('<head><base href="https://first.example/x/"><base href="https://second.example/">'
               '</head><body><a href="g">g</a></body>')
        self.assertEqual(extract(doc, "https://e.com/").links[0].url, "https://first.example/x/g")

        doc = '<head><base href="javascript:void(0)"></head><body><a href="/g">g</a></body>'
        self.assertEqual(extract(doc, "https://e.com/").links[0].url, "https://e.com/g")

    def test_non_document_schemes_are_excluded(self) -> None:
        doc = (
            '<body><a href="javascript:alert(1)">j</a><a href="JavaScript:x">J</a>'
            '<a href="mailto:a@b.c">m</a><a href="tel:+1234">t</a>'
            '<a href="data:text/html,<b>x">d</a><a href="#frag">f</a>'
            '<a href="ftp://f.example/x">p</a><a href="file:///etc/passwd">l</a>'
            '<a href="about:blank">a</a><a href="">e</a><a>none</a>'
            '<a href="/keep">k</a></body>'
        )
        page = extract(doc, "https://e.com/")
        self.assertEqual([link.url for link in page.links], ["https://e.com/keep"])

    def test_whitespace_inside_a_scheme_does_not_smuggle_javascript(self) -> None:
        page = extract('<body><a href="java\tscript:alert(1)">x</a></body>', "https://e.com/")
        self.assertEqual(page.links, [])

    def test_malformed_href_is_skipped_not_raised(self) -> None:
        page = extract('<body><a href="http://[::1">bad</a><a href="/ok">ok</a></body>',
                       "https://e.com/")
        self.assertEqual([link.url for link in page.links], ["https://e.com/ok"])

    def test_links_are_deduplicated_in_document_order(self) -> None:
        doc = ('<body><a href="/one">first text</a><a href="/two">second</a>'
               '<a href="/one">duplicate</a></body>')
        page = extract(doc, "https://e.com/")
        self.assertEqual([link.url for link in page.links],
                         ["https://e.com/one", "https://e.com/two"])
        self.assertEqual(page.links[0].text, "first text")

    def test_nofollow_is_flagged_and_filtered(self) -> None:
        doc = ('<body><a href="/a" rel="nofollow noopener">a</a><a href="/b" rel="noopener">b</a>'
               '<a href="/c" rel="NOFOLLOW">c</a></body>')
        page = extract(doc, "https://e.com/")
        self.assertEqual([link.nofollow for link in page.links], [True, False, True])
        self.assertEqual(page.outgoing(), ["https://e.com/b"])
        self.assertEqual(len(page.outgoing(follow_only=False)), 3)

    def test_links_inside_removed_boilerplate_are_still_returned(self) -> None:
        # The crawler discovers the next page through the nav we just deleted.
        doc = (f'<body><nav><a href="/next">next page</a></nav>'
               f"<div id=content>{paragraphs(3)}</div>"
               f'<footer><a href="/tos">terms</a></footer></body>')
        page = extract(doc, "https://e.com/")
        self.assertEqual([link.url for link in page.links],
                         ["https://e.com/next", "https://e.com/tos"])
        self.assertNotIn("terms", page.text)

    def test_link_text_is_flattened_to_one_line(self) -> None:
        page = extract('<body><a href="/x">foo<br>bar <b>baz</b></a></body>', "https://e.com/")
        self.assertEqual(page.links[0].text, "foo bar baz")

    def test_without_a_document_url_only_absolute_links_resolve(self) -> None:
        doc = '<body><a href="/rel">r</a><a href="https://e.com/abs">a</a></body>'
        self.assertEqual([link.url for link in extract(doc).links], ["https://e.com/abs"])

    def test_link_text_survives_in_the_prose(self) -> None:
        page = extract(f'<body><p>read <a href="/x">the docs</a> now. {PARA}</p></body>',
                       "https://e.com/")
        self.assertIn("read the docs now.", page.text)


# ------------------------------------------------------------------- metadata


class MetadataTestCase(unittest.TestCase):
    def test_first_title_wins(self) -> None:
        page = extract("<head><title>First</title><title>Second</title></head><body>x</body>")
        self.assertEqual(page.title, "First")

    def test_empty_first_title_falls_through(self) -> None:
        page = extract("<head><title> </title><title>Real</title></head><body>x</body>")
        self.assertEqual(page.title, "Real")

    def test_missing_title(self) -> None:
        self.assertEqual(extract("<body><p>no title here</p></body>").title, "")

    def test_svg_title_is_not_the_page_title(self) -> None:
        doc = ("<body><svg><title>icon label</title></svg></body>"
               "<head><title>Real Title</title></head>")
        self.assertEqual(extract(doc).title, "Real Title")

    def test_title_is_not_repeated_in_the_body_text(self) -> None:
        page = extract("<html><head><title>Site Title</title></head>"
                       "<body><p>Hello world here.</p></body></html>")
        self.assertEqual(page.title, "Site Title")
        self.assertEqual(page.text, "Hello world here.")

    def test_title_is_flattened_and_decoded(self) -> None:
        page = extract("<head><title>Docs\n  &amp; Guides</title></head>")
        self.assertEqual(page.title, "Docs & Guides")

    def test_og_title_overrides_the_title_tag(self) -> None:
        doc = ('<head><title>Tag</title><meta property="og:title" content="Open Graph"></head>')
        self.assertEqual(extract(doc).title, "Open Graph")

    def test_meta_is_collected_first_wins(self) -> None:
        doc = ('<head><meta name="description" content="real">'
               '<meta name="description" content="spam">'
               '<meta property="og:image" content="/i.png">'
               '<meta name="empty" content=""></head>')
        page = extract(doc)
        self.assertEqual(page.meta["description"], "real")
        self.assertEqual(page.meta["og:image"], "/i.png")
        self.assertNotIn("empty", page.meta)

    def test_canonical_first_wins_and_resolves_against_base(self) -> None:
        doc = ('<head><link rel="canonical" href="first.html">'
               '<link rel="canonical" href="/second">'
               '<base href="https://cdn.example.net/docs/"></head>')
        page = extract(doc, "https://e.com/dir/page")
        self.assertEqual(page.canonical, "https://cdn.example.net/docs/first.html")

    def test_canonical_rel_is_matched_per_token(self) -> None:
        doc = '<head><link rel="alternate canonical" href="/c"></head>'
        self.assertEqual(extract(doc, "https://e.com/").canonical, "https://e.com/c")
        doc = '<head><link rel="canonicalise" href="/c"></head>'
        self.assertEqual(extract(doc, "https://e.com/").canonical, "")

    def test_lang_first_wins(self) -> None:
        page = extract('<html lang="en-GB"><body><p>x</p></body></html>')
        self.assertEqual(page.lang, "en-GB")
        self.assertEqual(extract("<body><p>x</p></body>").lang, "")

    def test_published_from_time_then_meta(self) -> None:
        self.assertEqual(extract('<body><time datetime="2026-01-02">Jan</time></body>').published,
                         "2026-01-02")
        doc = ('<head><meta property="article:published_time" content="2026-03-04"></head>'
               '<body><time datetime="2026-01-02">x</time></body>')
        self.assertEqual(extract(doc).published, "2026-03-04")

    def test_jsonld_is_parsed_and_bad_json_is_skipped(self) -> None:
        doc = (
            '<head><script type="application/ld+json">{"@type": "Article"}</script>'
            '<script type="application/ld+json">{not json}</script>'
            '<script type="application/ld+json">   </script>'
            '<script type="text/javascript">{"@type": "NotLd"}</script></head>'
        )
        page = extract(doc)
        self.assertEqual(page.jsonld, [{"@type": "Article"}])

    def test_jsonld_nesting_bomb_is_survived(self) -> None:
        bomb = "[" * 20_000 + "]" * 20_000
        doc = (f'<head><script type="application/ld+json">{bomb}</script></head>'
               "<body><p>ok</p></body>")
        page = extract(doc)
        self.assertEqual(page.jsonld, [])
        self.assertEqual(page.text, "ok")

    def test_declared_charset_is_exposed(self) -> None:
        page = extract('<head><meta charset="ISO-8859-1"><title>t</title></head>')
        self.assertEqual(page.meta["charset"], "iso-8859-1")

    def test_declared_charset_from_http_equiv(self) -> None:
        doc = '<head><meta http-equiv="Content-Type" content="text/html; charset=Shift_JIS"></head>'
        self.assertEqual(extract(doc).meta["charset"], "shift_jis")

    def test_charset_disagreement_with_the_transport_is_visible(self) -> None:
        # The bytes are cp1252 but the header claimed utf-8, so the caller
        # decoded them the way `Response.text` does and handed us mojibake. The
        # document's own claim is the only way to explain it downstream.
        raw = '<head><meta charset="windows-1252"><title>café</title></head>'.encode("cp1252")
        page = extract(raw.decode("utf-8", "replace"))
        self.assertEqual(page.meta["charset"], "windows-1252")
        self.assertNotEqual(page.title, "café")

    def test_byte_order_mark_is_not_content(self) -> None:
        page = extract("﻿<html><head><title>B</title></head><body><p>body text</p></body></html>")
        self.assertEqual(page.title, "B")
        self.assertEqual(page.text, "body text")


# ------------------------------------------------------------------- hostile


HOSTILE = """﻿<!DOCTYPE html>
<html lang=en>
<head>
<title>Hostile &amp; Broken</title>
<base href="https://cdn.example.net/base/">
<meta charset="utf-8">
<meta property="og:description" content="a page that fights back">
<link rel=canonical href=canon.html>
<script>var trap = "</div></body><p>injected paragraph</p>"; if (1 < 2) { go(); }</script>
<script type="application/ld+json">{"@type": "WebPage", "name": "H"}</script>
<style>.nav::after { content: "</style>"; }</style>
</head>
<body>
<nav class=site-nav><a href=/one>One</a><a href='javascript:void(0)'>JS</a>
<a href="#top">Top</a></nav>
<!-- <div class="content"><p>commented out article</p></div> -->
<div class=post-content>
<h1>Real   Heading</h1>
<p>First real paragraph, which is long enough that the scorer treats it as the
body of the document rather than as an aside or a caption.</p>
</span></div></div>
<p>Second real paragraph, also long enough to matter, with an <a href=next.html>onward
link</a> inside it.</p>
<blockquote><p>quoted one</p><p>quoted two</p></blockquote>
<pre><code class="language-md">```
fenced inside a fence
```</code></pre>
<table><tr><td>cell a<td>cell b</table>
<ul><li>item one<li>item two</ul>
<svg><title>icon</title></svg>
<![CDATA[ cdata payload ]]>
<div hidden>hidden payload</div>
<footer class=legal>&copy; 2026 Example <a href="/tos" rel="nofollow">Terms</a></footer>
<div class="teaser" data-x="unterminated
"""


class HostileDocumentTestCase(unittest.TestCase):
    """One document with every trap at once, parsed exactly as it arrives."""

    def setUp(self) -> None:
        self.page = extract(HOSTILE, "https://e.com/dir/page.html")

    def test_metadata(self) -> None:
        self.assertEqual(self.page.title, "Hostile & Broken")
        self.assertEqual(self.page.lang, "en")
        self.assertEqual(self.page.canonical, "https://cdn.example.net/base/canon.html")
        self.assertEqual(self.page.meta["charset"], "utf-8")
        self.assertEqual(self.page.jsonld, [{"@type": "WebPage", "name": "H"}])

    def test_the_article_survives(self) -> None:
        self.assertIn("First real paragraph", self.page.text)
        self.assertIn("Second real paragraph", self.page.text)
        self.assertEqual(self.page.headings, [(1, "Real Heading")])

    def test_nothing_leaks_out_of_scripts_comments_or_hidden_nodes(self) -> None:
        for leak in ("injected paragraph", "var trap", "commented out", "cdata payload",
                     "hidden payload", "content:", "icon"):
            with self.subTest(leak=leak):
                self.assertNotIn(leak, self.page.text)

    def test_boilerplate_is_gone_but_its_links_are_not(self) -> None:
        self.assertNotIn("Terms", self.page.text)
        self.assertNotIn("One", self.page.text.split())
        self.assertEqual(
            [link.url for link in self.page.links],
            [
                "https://cdn.example.net/one",
                "https://cdn.example.net/base/next.html",
                "https://cdn.example.net/tos",
            ],
        )
        self.assertTrue(self.page.links[-1].nofollow)
        self.assertEqual(self.page.outgoing(), self.page.outgoing(follow_only=False)[:2])

    def test_structure_is_preserved(self) -> None:
        self.assertIn("> quoted one", self.page.markdown)
        self.assertIn("> quoted two", self.page.markdown)
        self.assertIn("| cell a | cell b |", self.page.markdown)
        self.assertIn("- item one", self.page.markdown)
        self.assertIn("````md\n```\nfenced inside a fence\n```\n````", self.page.markdown)

    def test_the_truncated_tail_is_not_content(self) -> None:
        self.assertNotIn("unterminated", self.page.text)
        self.assertNotIn("data-x", self.page.text)


# ---------------------------------------------------------------- degradation


class DegradationTestCase(unittest.TestCase):
    def test_a_render_failure_still_returns_metadata_and_links(self) -> None:
        doc = ('<html lang="fr"><head><title>Still Here</title>'
               '<link rel="canonical" href="/c"></head>'
               f'<body><a href="/x">x</a>{paragraphs(2)}</body></html>')
        with mock.patch.object(html_mod, "_find_main", side_effect=RuntimeError("boom")):
            page = extract(doc, "https://e.com/")
        self.assertEqual(page.title, "Still Here")
        self.assertEqual(page.lang, "fr")
        self.assertEqual(page.canonical, "https://e.com/c")
        self.assertEqual([link.url for link in page.links], ["https://e.com/x"])
        self.assertEqual(page.text, "")
        self.assertEqual(page.markdown, "")

    def test_a_recursion_failure_is_caught(self) -> None:
        with mock.patch.object(html_mod, "_prune", side_effect=RecursionError):
            page = extract(f"<body>{paragraphs(2)}</body>", "https://e.com/")
        self.assertEqual(page.text, "")

    def test_the_thin_page_fallback_still_carries_the_links(self) -> None:
        # This document only survives via the conservative retry; the retry
        # builds a second page, and it must not come back link-less.
        page = extract(f"<body><nav>{anchors(3)}</nav></body>", "https://e.com/")
        self.assertEqual(len(page.links), 3)
        self.assertIn("Section number 1", page.text)


# --------------------------------------------------------------- page methods


class ExtractedPageTestCase(unittest.TestCase):
    def test_word_count(self) -> None:
        self.assertEqual(ExtractedPage("u", "t", "one two  three\nfour", "").word_count, 4)
        self.assertEqual(ExtractedPage("u", "t", "", "").word_count, 0)

    def test_link_density_of_an_empty_page(self) -> None:
        page = ExtractedPage("u", "t", "", "", links=[Link("https://e.com/", "text")])
        self.assertEqual(page.link_density, 0.0)

    def test_link_density_is_clamped(self) -> None:
        page = ExtractedPage("u", "t", "abc", "", links=[Link("https://e.com/", "x" * 99)])
        self.assertEqual(page.link_density, 1.0)

    def test_link_density_of_a_real_page(self) -> None:
        page = ExtractedPage("u", "t", "a" * 100, "", links=[Link("https://e.com/", "x" * 25)])
        self.assertAlmostEqual(page.link_density, 0.25)

    def test_outgoing_filters_nofollow_by_default(self) -> None:
        page = ExtractedPage(
            "u", "t", "text", "",
            links=[Link("https://e.com/a", "a"), Link("https://e.com/b", "b", "nofollow", True)],
        )
        self.assertEqual(page.outgoing(), ["https://e.com/a"])
        self.assertEqual(page.outgoing(follow_only=False), ["https://e.com/a", "https://e.com/b"])


if __name__ == "__main__":
    unittest.main()
