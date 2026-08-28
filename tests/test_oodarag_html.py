"""HTML extraction: the tolerant tree builder, boilerplate removal, markdown.

The load-bearing property of this module is "degrade, don't die": every input
here is a page a real crawl hits, and none of them may raise. Several tests
below are regressions - each says which failure it pins and what that failure
cost downstream, because "this was wrong" is not a reason to keep a test.

No network: `extract` is a pure function of a string, so the whole module is
driven from literal HTML. Nothing here needs an HttpClient.
"""

from __future__ import annotations

import unittest

from oodarag.scrape.html import (
    _MAX_TREE_DEPTH,
    _find_main,
    _parse,
    _prune,
    extract,
)

# A page shaped like the Sphinx/ReadTheDocs output this crawler was built for:
# an ARIA-labelled sidebar of navigation, a role="main" body, a footer, and a
# head carrying metadata in three competing vocabularies.
DOCS_PAGE = """<!doctype html>
<html lang="en">
<head>
  <title>Chunking &mdash; oodarag 0.1 documentation</title>
  <meta property="og:title" content="Chunking strategies">
  <meta name="description" content="How oodarag splits documents for retrieval.">
  <meta property="article:published_time" content="2024-03-01T09:00:00Z">
  <link rel="canonical" href="/en/latest/chunking.html">
  <script type="application/ld+json">{"@type": "TechArticle", "headline": "Chunking"}</script>
  <script type="application/ld+json">{"@type": "TechArticle", headline: broken,}</script>
  <style>.wy-nav-side { display: block }</style>
</head>
<body>
  <div class="wy-nav-side" role="navigation" aria-label="main navigation">
    <ul>
      <li><a href="/en/latest/install.html">Installation</a></li>
      <li><a href="/en/latest/ingest.html">Ingesting documents</a></li>
    </ul>
  </div>
  <div class="wy-nav-content">
    <div class="rst-content" role="main">
      <h1>Chunking</h1>
      <p>A chunker splits a document into passages that a retriever can rank.
         Read the <a href="/en/latest/retrieval.html">retrieval guide</a> before
         tuning any of the sizes described on this page, because the two stages
         are budgeted together and changing one moves the other.</p>
      <h2>Fixed windows</h2>
      <p>The simplest chunker takes a fixed number of tokens with an overlap,
         which is cheap, predictable, and wrong at every heading boundary.</p>
      <pre><code class="language-python">def chunk(text, size=512):
    words = text.split()
    return [words[i:i + size] for i in range(0, len(words), size)]
</code></pre>
    </div>
  </div>
  <footer class="footer">
    <a href="/legal.html" rel="nofollow">Legal</a>
    <time datetime="2024-01-01">Last built 2024</time>
  </footer>
</body>
</html>"""


def md(html: str, url: str = "https://ex.com/a/page.html", **kw) -> str:
    return extract(html, url, **kw).markdown


def prose(n: int = 8) -> str:
    """A paragraph long enough to clear the 140-character candidate floor."""
    return "<p>" + "Prose sentence about widgets. " * n + "</p>"


class TestTreeBuilderRecovery(unittest.TestCase):
    """The recovery rules are what keep a malformed page from truncating."""

    def test_a_stray_close_tag_does_not_unwind_the_stack(self):
        # The stated single most common cause of truncated extractions: an
        # extra </div> pops a scope that was never opened, and on a real page
        # everything after it lands outside the body and is thrown away.
        page = extract(
            "<html><body><div><p>one</p></div></div><p>two</p><p>three</p></body></html>",
            "https://ex.com/a",
        )
        self.assertIn("two", page.text)
        self.assertIn("three", page.text)

    def test_unclosed_paragraphs_stay_separate_blocks(self):
        # <p> without </p> is legal HTML and extremely common; welding the
        # paragraphs together would hand the chunker one undifferentiated blob.
        out = md("<html><body><p>First para<p>Second para<p>Third para</body></html>")
        self.assertEqual(out, "First para\n\nSecond para\n\nThird para")

    def test_a_block_tag_implicitly_closes_an_open_paragraph(self):
        out = md("<html><body><p>Lead in<ul><li>item one</li></ul></body></html>")
        self.assertIn("Lead in", out)
        self.assertIn("- item one", out)
        # The list must not have been swallowed into the paragraph's line.
        self.assertNotIn("Lead in - item one", out)

    def test_li_closes_the_previous_li(self):
        out = md("<html><body><ul><li>one<li>two<li>three</ul></body></html>")
        self.assertEqual(out, "- one\n- two\n- three")

    def test_a_matching_close_tag_closes_everything_opened_inside_it(self):
        out = md("<html><body><div><p>inside <span>span text</div><p>after</body></html>")
        self.assertIn("inside span text", out)
        self.assertIn("after", out)

    def test_void_and_self_closed_tags_open_no_scope(self):
        # If <img> or <br/> opened a scope, every following sibling would nest
        # inside it and one unclosed void tag would swallow the rest of the page.
        out = md('<html><body><p>a<br><img src="x.png" alt="a chart"><br/>b</p>'
                 "<p>next block</p></body></html>")
        self.assertIn("[image: a chart]", out)
        self.assertIn("next block", out)

    def test_deeply_nested_unclosed_tags_do_not_exhaust_the_stack(self):
        # Regression. Every stage walks the tree recursively and the fallback
        # build used copy.deepcopy, which costs about six frames per level, so
        # a page nested ~150 deep raised RecursionError out of extract() - a
        # crawl died on a broken page instead of degrading on it. Unclosed
        # inline tags are the realistic source: each one opens a new scope.
        html = "<html><body>" + "<span>" * 5000 + "the text that matters"
        page = extract(html, "https://ex.com/a")
        self.assertIn("the text that matters", page.text)

    def test_the_depth_cap_still_records_the_element(self):
        # Past the cap an element opens no scope, but its content must still
        # reach the output - flattening structure is the acceptable loss here.
        builder = _parse("<html><body>" + "<div>" * (_MAX_TREE_DEPTH + 50) + "deep text")
        self.assertLessEqual(len(builder.stack), _MAX_TREE_DEPTH)
        self.assertIn("deep text", _render_all(builder))


def _render_all(builder) -> str:
    """Flatten a built tree to its text, for assertions about the tree itself."""
    out: list[str] = []
    for node in builder.root.iter_nodes():
        out.extend(c for c in node.children if isinstance(c, str))
    return " ".join(out)


class TestWhitespace(unittest.TestCase):
    def test_pre_keeps_newlines_and_indentation(self):
        # Collapsing whitespace inside a code block changes what the code means;
        # in Python it changes whether it parses at all.
        out = md("<html><body><article>" + prose() + "<pre><code>def f():\n"
                 "    if x:\n"
                 "        return 1\n"
                 "</code></pre></article></body></html>")
        self.assertIn("```\ndef f():\n    if x:\n        return 1\n```", out)

    def test_whitespace_between_inline_elements_is_a_word_boundary(self):
        # The failure this prevents: dropping the whitespace-only text node
        # between two inline elements welds "read the" + "docs" into
        # "read thedocs", which no tokenizer recovers from.
        out = md("<html><body><p><span>read the</span> <a href='/d'>docs</a>"
                 " <em>now</em></p></body></html>")
        self.assertIn("read the docs now", out)
        self.assertNotIn("thedocs", out)

    def test_paragraph_boundary_inside_a_quote_is_a_word_boundary(self):
        # Regression, same failure one level up: a blockquote is flattened with
        # _inline_text, and minified markup has no text node between </p><p>,
        # so a two-paragraph pull quote came out as "First.Second."
        out = md("<html><body><article>" + prose() +
                 "<blockquote><p>First point.</p><p>Second point.</p></blockquote>"
                 "</article></body></html>")
        self.assertIn("> First point.\n> Second point.", out)
        self.assertNotIn("First point.Second point.", out)

    def test_a_table_cell_never_breaks_its_row(self):
        # A cell holding block content must still render as one line, or the
        # row ends mid-table and the remaining cells become loose prose.
        out = md("<html><body><article>" + prose() + "<table><tr><td><p>one</p><p>two</p></td>"
                 "<td>three</td></tr></table></article></body></html>")
        self.assertIn("| one two | three |", out)


class TestBoilerplateRemoval(unittest.TestCase):
    def test_chrome_is_dropped_from_the_text(self):
        html = ("<html><body>"
                "<div role='navigation'><p>Home About Contact us here</p></div>"
                "<div aria-hidden='true'><p>decorative junk text</p></div>"
                "<div style='display: none'><p>invisible text</p></div>"
                "<div class='cookie-banner'><p>We use cookies on this site</p></div>"
                "<div class='sidebar'><p>Recent posts listed here</p></div>"
                "<article>" + prose() + "</article></body></html>")
        text = extract(html, "https://ex.com/a").text
        for gone in ("Contact us", "decorative junk", "invisible text",
                     "We use cookies", "Recent posts"):
            self.assertNotIn(gone, text)
        self.assertIn("Prose sentence about widgets.", text)

    def test_a_class_matching_both_noise_and_content_is_kept(self):
        # "sidebar-content" matches the chrome pattern and the content pattern.
        # Dropping on the chrome match alone deletes the body of every site
        # whose wrapper happens to carry both words.
        text = extract("<html><body><div class='sidebar-content'>" + prose() +
                       "</div></body></html>", "https://ex.com/a").text
        self.assertIn("Prose sentence about widgets.", text)

    def test_an_article_wrapped_in_a_sidebar_still_extracts(self):
        # The conservative retry. Aggressive removal deletes class="sidebar"
        # outright, leaving nothing; returning an empty page for a page that
        # plainly has an article is worse than keeping some chrome with it.
        page = extract("<html><body><div class='sidebar'>" + prose() +
                       "</div></body></html>", "https://ex.com/a")
        self.assertIn("Prose sentence about widgets.", page.text)
        self.assertGreater(page.word_count, 25)

    def test_a_page_that_is_only_chrome_degrades_rather_than_dies(self):
        # Nothing survives aggressive removal and the retry does not help much
        # either; the contract is that this returns a page, not that it raises.
        page = extract("<html><body><nav><a href='/a'>A</a></nav></body></html>",
                       "https://ex.com/a")
        self.assertEqual(page.markdown, "A")
        self.assertEqual([link.url for link in page.links], ["https://ex.com/a"])


class TestLinkCollection(unittest.TestCase):
    def test_navigation_links_survive_for_the_crawler(self):
        # Regression, two shapes of one bug. Links were collected after the
        # aggressive prune, so every <nav> link was deleted before the crawler
        # saw it; the ARIA spelling, <div role="navigation">, was dropped even
        # earlier, in the conservative pass. A documentation site's link graph
        # is almost entirely navigation, so the crawl starved at depth one.
        html = ("<html><body>"
                "<nav><a href='/nav-link'>Nav</a></nav>"
                "<div role='navigation'><a href='/aria-link'>Aria</a></div>"
                "<article>" + prose() + "<a href='/body-link'>Body</a></article>"
                "<footer><a href='/footer-link'>Footer</a></footer>"
                "</body></html>")
        page = extract(html, "https://ex.com/a/page.html")
        self.assertEqual(
            [link.url for link in page.links],
            ["https://ex.com/nav-link", "https://ex.com/aria-link",
             "https://ex.com/body-link", "https://ex.com/footer-link"],
        )
        # ...and the chrome text is still out of the extracted body.
        self.assertNotIn("Nav", page.text)
        self.assertNotIn("Footer", page.text)

    def test_hidden_and_scripted_links_stay_out(self):
        # The first prune exists to drop these before links are collected: a
        # display:none link is a trap for crawlers, and a URL inside a <script>
        # string is not a link at all.
        html = ("<html><body>"
                "<div style='display:none'><a href='/hidden'>h</a></div>"
                "<div hidden><a href='/hidden2'>h2</a></div>"
                "<script>var s = '<a href=\"/scripted\">x</a>';</script>"
                "<p>Body text worth keeping here.</p>"
                "<a href='/real'>real</a></body></html>")
        page = extract(html, "https://ex.com/a")
        self.assertEqual([link.url for link in page.links], ["https://ex.com/real"])

    def test_non_navigable_schemes_and_duplicates_are_filtered(self):
        html = ("<html><body><p>text</p>"
                "<a href='mailto:a@b.com'>mail</a>"
                "<a href='javascript:void(0)'>js</a>"
                "<a href='#section'>anchor</a>"
                "<a href='../up.html'>up</a>"
                "<a href='/a/../up.html'>same page again</a>"
                "<a href='/out' rel='nofollow noopener'>out</a>"
                "</body></html>")
        page = extract(html, "https://ex.com/a/page.html")
        self.assertEqual([link.url for link in page.links],
                         ["https://ex.com/up.html", "https://ex.com/out"])
        self.assertTrue(page.links[1].nofollow)
        self.assertEqual(page.outgoing(), ["https://ex.com/up.html"])
        self.assertEqual(len(page.outgoing(follow_only=False)), 2)

    def test_link_density_measures_the_body_not_the_chrome(self):
        # Regression. link_density is written into every document's metadata as
        # a quality signal, and once `links` became page-wide it was dividing
        # navigation link text by body text: it read high precisely when
        # boilerplate removal had worked. It must measure the extracted body.
        page = extract(DOCS_PAGE, "https://ex.com/en/latest/chunking.html")
        self.assertGreater(len(page.links), len(page.body_links))
        self.assertEqual([link.text for link in page.body_links], ["retrieval guide"])
        self.assertLess(page.link_density, 0.15)

    def test_link_density_is_high_when_the_body_really_is_links(self):
        links = "".join(f"<p><a href='/p{i}'>Result number {i} title</a></p>" for i in range(12))
        page = extract(f"<html><body><div class='results'>{links}</div></body></html>",
                       "https://ex.com/a")
        self.assertGreater(page.link_density, 0.8)


class TestFindMain(unittest.TestCase):
    def _main_of(self, html: str, aggressive: bool = True):
        builder = _parse(html)
        _prune(builder.root, False)
        if aggressive:
            _prune(builder.root, True)
        return _find_main(builder.root)

    def test_main_wins_when_it_carries_enough_text(self):
        node = self._main_of(f"<html><body><div class='wrap'><main>{prose()}</main>"
                             f"<div class='other'>{prose()}</div></div></body></html>")
        self.assertEqual(node.tag, "main")

    def test_an_almost_empty_main_does_not_win(self):
        # Semantic markup is a hint, not a promise: sites wrap a spinner in
        # <main> and render the article beside it.
        node = self._main_of("<html><body><main><p>Loading</p></main>"
                             f"<div class='post'>{prose()}</div></body></html>")
        self.assertEqual(node.attrs.get("class"), "post")

    def test_the_tighter_container_wins_over_its_parent(self):
        # A parent always contains its child's text, so without the depth
        # nudge the outermost wrapper - and all the chrome in it - always wins.
        node = self._main_of(f"<html><body><div class='outer'><div class='inner'>"
                             f"{prose()}{prose()}</div></div></body></html>")
        self.assertEqual(node.attrs.get("class"), "inner")

    def test_a_nav_heavy_div_loses_to_a_prose_div(self):
        nav = "".join(f"<a href='/p{i}'>Page {i} of the manual</a>" for i in range(14))
        node = self._main_of(f"<html><body><div class='col'><div class='listing'>{nav}</div>"
                             f"<div class='prose'>{prose()}{prose()}</div></div></body></html>")
        self.assertEqual(node.attrs.get("class"), "prose")


class TestMarkdownFidelity(unittest.TestCase):
    def test_headings_are_rendered_and_reported(self):
        page = extract("<html><body><article><h1>Title</h1><p>Lead paragraph.</p>"
                       "<h2>Section</h2><p>Body.</p><h3>Sub</h3><p>More.</p>"
                       "<h2></h2></article></body></html>", "https://ex.com/a")
        self.assertIn("# Title", page.markdown)
        self.assertIn("## Section", page.markdown)
        self.assertIn("### Sub", page.markdown)
        # An empty heading is not a heading; a chunker splitting on it would
        # produce a section with no name.
        self.assertEqual(page.headings, [(1, "Title"), (2, "Section"), (3, "Sub")])
        # The plain-text view drops the markers but keeps the words.
        self.assertTrue(page.text.startswith("Title"))
        self.assertNotIn("#", page.text)

    def test_nested_lists_keep_the_indent_that_makes_them_nested(self):
        # Regression. _tidy collapsed runs of spaces everywhere, including the
        # leading indent, so "  - Inner" became " - Inner": one space is below
        # the parent item's content column, so every sub-item was promoted to a
        # sibling and a three-level API reference came out flat.
        out = md("<html><body><article>" + prose() +
                 "<ul><li>Outer<ul><li>Inner<ol><li>Deepest</li></ol></li></ul></li>"
                 "<li>Second</li></ul></article></body></html>")
        self.assertIn("\n- Outer\n  - Inner\n    1. Deepest\n- Second", out)

    def test_code_fences_carry_the_language_from_the_class(self):
        out = md("<html><body><article>" + prose() +
                 "<pre><code class='highlight language-python'>x = 1</code></pre>"
                 "</article></body></html>")
        self.assertIn("```python\nx = 1\n```", out)

    def test_a_code_block_without_a_language_still_fences(self):
        out = md("<html><body><article>" + prose() +
                 "<pre>plain listing</pre></article></body></html>")
        self.assertIn("```\nplain listing\n```", out)

    def test_a_table_renders_as_a_table(self):
        # Regression. Without the delimiter row under the header, GFM does not
        # see a table at all: every row renders as literal pipe characters, and
        # the column structure the answer needs is gone.
        out = md("<html><body><article>" + prose() +
                 "<table><thead><tr><th>Option</th><th>Default</th></tr></thead>"
                 "<tbody><tr><td>size</td><td>512</td></tr></tbody></table>"
                 "</article></body></html>")
        self.assertIn("| Option | Default |\n| --- | --- |\n| size | 512 |", out)

    def test_rules_images_and_quotes_survive(self):
        out = md("<html><body><article>" + prose() +
                 "<hr><p>After <img src='d.png' alt='a diagram'> the rule.</p>"
                 "<blockquote>Quoted line.</blockquote></article></body></html>")
        self.assertIn("\n---\n", out)
        self.assertIn("[image: a diagram]", out)
        self.assertIn("> Quoted line.", out)

    def test_an_image_without_alt_text_leaves_no_placeholder(self):
        out = md("<html><body><p>before <img src='spacer.gif'> after</p></body></html>")
        self.assertEqual(out, "before after")


class TestMetadata(unittest.TestCase):
    def setUp(self):
        self.page = extract(DOCS_PAGE, "https://ex.com/en/latest/chunking.html")

    def test_og_title_beats_the_title_element(self):
        # Sites suffix <title> with the site name for search results; og:title
        # is the one they wrote for humans quoting the page.
        self.assertEqual(self.page.title, "Chunking strategies")

    def test_the_title_element_is_used_when_there_is_no_og_title(self):
        page = extract("<html><head><title>Just a title</title></head>"
                       "<body><p>short body</p></body></html>", "https://ex.com/a")
        self.assertEqual(page.title, "Just a title")

    def test_the_title_is_not_repeated_as_body_text(self):
        # Regression. On any page too short for _find_main to pick a container,
        # the document root was rendered - <head> and all - so the title was
        # welded onto the front of the body, inflating word_count and changing
        # the content hash the crawler dedupes on.
        page = extract("<html><head><title>My Title</title></head>"
                       "<body><p>Short body text here.</p></body></html>", "https://ex.com/a")
        self.assertEqual(page.markdown, "Short body text here.")
        self.assertEqual(page.title, "My Title")

    def test_canonical_is_resolved_against_the_fetched_url(self):
        self.assertEqual(self.page.canonical, "https://ex.com/en/latest/chunking.html")

    def test_lang_and_meta_names_are_kept(self):
        self.assertEqual(self.page.lang, "en")
        self.assertEqual(self.page.meta["description"],
                         "How oodarag splits documents for retrieval.")

    def test_published_time_prefers_the_declared_metadata(self):
        # <time> in a footer is usually the build date, not the publication
        # date; article:published_time is the page's own statement.
        self.assertEqual(self.page.published, "2024-03-01T09:00:00Z")

    def test_a_time_element_is_the_fallback(self):
        page = extract("<html><body><article><time datetime='2020-05-06'>May</time>"
                       "<p>Body text.</p></article></body></html>", "https://ex.com/a")
        self.assertEqual(page.published, "2020-05-06")

    def test_valid_json_ld_is_parsed_and_a_broken_block_is_skipped(self):
        # Hand-templated JSON-LD is malformed often enough that raising on it
        # would lose the whole page over a block nothing downstream requires.
        self.assertEqual(self.page.jsonld, [{"@type": "TechArticle", "headline": "Chunking"}])

    def test_entities_are_decoded_in_the_title(self):
        page = extract("<html><head><title>A &amp; B &mdash; C</title></head>"
                       "<body><p>x</p></body></html>", "https://ex.com/a")
        self.assertEqual(page.title, "A & B \u2014 C")


class TestRealisticPage(unittest.TestCase):
    def setUp(self):
        self.page = extract(DOCS_PAGE, "https://ex.com/en/latest/chunking.html")

    def test_the_body_is_extracted_and_the_chrome_is_not(self):
        self.assertIn("A chunker splits a document into passages", self.page.text)
        self.assertNotIn("Installation", self.page.text)
        self.assertNotIn("Legal", self.page.text)
        self.assertNotIn("Last built", self.page.text)

    def test_structure_that_a_chunker_splits_on_is_preserved(self):
        self.assertEqual(self.page.headings, [(1, "Chunking"), (2, "Fixed windows")])
        self.assertIn("```python\ndef chunk(text, size=512):", self.page.markdown)
        # The code block keeps its indentation: dedented, this snippet is a
        # different program.
        self.assertIn("\n    words = text.split()", self.page.markdown)

    def test_word_count_counts_the_body(self):
        self.assertGreater(self.page.word_count, 60)
        self.assertLess(self.page.word_count, 120)

    def test_every_link_on_the_page_reaches_the_crawler(self):
        self.assertEqual(
            [link.url for link in self.page.links],
            ["https://ex.com/en/latest/install.html",
             "https://ex.com/en/latest/ingest.html",
             "https://ex.com/en/latest/retrieval.html",
             "https://ex.com/legal.html"],
        )
        self.assertEqual(self.page.outgoing()[-1], "https://ex.com/en/latest/retrieval.html")


class TestMalformedInputNeverRaises(unittest.TestCase):
    """Every one of these is a page a crawl actually meets."""

    CASES = {
        "empty": "",
        "not html": "just a bare sentence with no tags at all",
        "unclosed everything": "<html><body><div><p><span>text",
        "pre that never closes": "<html><body><pre>code\n  indented\nmore",
        "unquoted attributes": "<html><body><div class=main id=top><p>text</p></div>",
        "stray less-than in text": "<html><body><p>if a < b and 5<6 then</p></body></html>",
        "close tags only": "</div></p></body></html>",
        "attribute with no value": "<html><body><div hidden data-x><p>text</p></div>",
        "nested table soup": "<table><tr><td><table><tr><td>x</table></td></tr>",
        "script never closed": "<html><body><p>before</p><script>var x = 1;",
        "broken json-ld": '<script type="application/ld+json">{,,}</script><p>text</p>',
        "comment then content": "<html><!-- <p>commented</p> --><body><p>real</p></body>",
        "bad char refs": "<html><body><p>a &notareal; b &#xZZ; c</p></body></html>",
        "doctype only": "<!doctype html>",
        "cdata": "<html><body><![CDATA[raw]]><p>text</p></body></html>",
    }

    def test_no_input_raises(self):
        for label, html in self.CASES.items():
            with self.subTest(label):
                page = extract(html, "https://ex.com/a")
                self.assertIsInstance(page.markdown, str)
                self.assertIsInstance(page.text, str)
                self.assertIsInstance(page.links, list)

    def test_content_after_the_damage_is_still_recovered(self):
        # Not dying is half the promise; the other half is that the page after
        # the malformed part is still extracted rather than silently truncated.
        self.assertIn("text", extract(self.CASES["unclosed everything"], "").text)
        self.assertIn("real", extract(self.CASES["comment then content"], "").text)
        self.assertIn("before", extract(self.CASES["script never closed"], "").text)
        self.assertIn("if a < b", extract(self.CASES["stray less-than in text"], "").text)

    def test_an_empty_page_reports_zero_rather_than_dividing_by_it(self):
        page = extract("", "https://ex.com/a")
        self.assertEqual(page.word_count, 0)
        self.assertEqual(page.link_density, 0.0)


if __name__ == "__main__":
    unittest.main()
