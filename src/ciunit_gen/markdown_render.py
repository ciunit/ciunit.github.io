"""Markdown → HTML for post bodies, and nothing else.

This is the one place in the generator where autoescaping is bypassed, so it is
worth saying plainly why that is safe here and why it is not licence to loosen
`model._paragraphs`.

Publication YAML is plain text by design: those files carry scientific claims
that get quoted and cited, and the prose fields are lists of paragraphs
precisely so that no content file can inject markup into a citable page.
Cross-references there go through the structured `links`/`related` fields.

Posts are a different kind of writing. An essay that cannot link a phrase, quote
an email, or put a table in the middle of an argument is not an essay. So post
bodies are Markdown, rendered here and handed to Jinja as `Markup`. The input is
in-repo, authored, and reviewed in a pull request like any other source file —
the same trust we already extend to the hand-written pages under `docs/`. The
escape hatch stays confined to this module: `render_markdown` is the only
function that returns `Markup` from content, and `posts.py` is the only caller.
"""
from __future__ import annotations

import re

import markdown
from markupsafe import Markup

# `extra` brings tables, definition lists, and fenced code; `smarty` gives the
# curly quotes and em dashes the hand-written pages already have; `sane_lists`
# stops a stray "1." in prose from opening an ordered list.
_EXTENSIONS = ["extra", "smarty", "sane_lists"]

# Our own domain, plus the localhost form used when previewing with
# `python -m http.server`. Everything else is off-site.
_INTERNAL = re.compile(r"^https?://(?:[a-z0-9-]+\.)*ciunit\.org(?:[/?#]|$)", re.I)

_HREF = re.compile(r'<a\s+([^>]*?)href="([^"]+)"([^>]*?)>', re.I)


def _external_links(html: str) -> str:
    """Add target/rel to every off-domain link.

    CLAUDE.md requires `target="_blank" rel="noopener noreferrer"` on any link
    leaving ciunit.org, and Markdown link syntax has no way to say so. Enforcing
    it here means a post author writes ordinary Markdown and cannot get it
    wrong, which is the same reason figure credit lines are generated rather
    than typed.
    """
    def fix(m: re.Match) -> str:
        before, href, after = m.group(1), m.group(2), m.group(3)
        attrs = f"{before}{after}"
        if not href.lower().startswith(("http://", "https://")):
            return m.group(0)          # relative or mailto: — left alone
        if _INTERNAL.match(href):
            return m.group(0)
        if "target=" in attrs.lower():
            return m.group(0)          # already set by hand, don't double it
        return f'<a {before}href="{href}"{after} target="_blank" rel="noopener noreferrer">'

    return _HREF.sub(fix, html)


def render_markdown(text: str) -> Markup:
    """Render one chunk of post Markdown to trusted HTML."""
    # A fresh converter per call: markdown.Markdown instances carry state
    # between conversions (footnote counters, reference definitions), and a
    # shared one would leak a post's footnotes into the next post's page.
    html = markdown.markdown(text, extensions=_EXTENSIONS, output_format="html")
    return Markup(_external_links(html))


def render_inline(text: str) -> Markup:
    """Render a caption or byline fragment, without the wrapping <p>.

    Figure captions are one sentence with links and emphasis in them; a <p>
    inside <figcaption> would take the paragraph margins of body copy.
    """
    html = render_markdown(text)
    m = re.fullmatch(r"<p>(.*)</p>", str(html).strip(), re.S)
    return Markup(m.group(1)) if m else html
