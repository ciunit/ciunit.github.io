"""Content model for "What We Are Thinking" — the posts section.

Loads `content/posts/*.md`: YAML front matter for the metadata, Markdown for the
body. Posts are commentary, not publications, so the schema differs from
`model.Paper` in three ways that matter:

* **The body is Markdown**, because an essay needs links, emphasis, block quotes
  and tables mid-argument. See `markdown_render` for why that escape hatch is
  safe here and does not extend to publication YAML.
* **Posts are signed and dated.** `authors` and `date` are required and render
  as a byline under the title. Authorship of a post is personal in a way a
  multi-author paper is not, and other people will write posts here later — a
  reader has to be able to see whose view this is.
* **`about` is optional.** A post about one of our publications links to its
  page; a post about someone else's work, or about no single paper, simply
  omits it.

Everything the publications loader is strict about, this one is strict about
too: a post with no `description` or no self-contained `key_point` is a page
that degrades into noise, and a figure with no alt text is invisible to the
retrieval systems the section exists to be read by.
"""
from __future__ import annotations

import datetime as _dt
import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml
from markupsafe import Markup

from .markdown_render import render_inline, render_markdown
from .model import ContentError, Figure, _require

# Posts carry a full date, not a bare year: they are dated writing, and the
# byline prints the day. Stricter than model.DATE_RE on purpose.
POST_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")

REQUIRED_POST = ("slug", "title", "date", "authors", "description", "key_point")

# A figure needs a file and alt text always; credit and licence too unless the
# image is ours, which `own: true` asserts.
REQUIRED_POST_FIGURE = ("file", "alt")

# Front matter is delimited the way the Jekyll source delimits it, so a post
# body can be lifted across with its opening lines intact.
FRONT_MATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n?(.*)\Z", re.S)

# ':::figure' … ':::' — a block-level fence whose contents are YAML. Keeping the
# figure structured rather than letting Markdown emit a bare <img> is what keeps
# alt text required and the credit line generated instead of hand-typed.
FENCE_RE = re.compile(r"^:::(\w+)[ \t]*\n(.*?)^:::[ \t]*$", re.M | re.S)


@dataclass
class Prose:
    """A run of body Markdown, already rendered."""
    html: Markup
    kind: str = "prose"


@dataclass
class PostFigure:
    """An image in a post body.

    `own: true` means the image is ours — a figure Ken made, a screenshot, a
    plot from our own code — and so carries no credit line. Anything lifted from
    a publication needs `credit` and `license`, and the sentence under it is
    assembled by `model.Figure.credit_line` rather than typed, for the same
    reason publication figures are: that is how a wrong licence ends up under an
    image.
    """
    file: str
    alt: str
    caption: str = ""
    credit: str = ""
    license: str = ""
    license_url: str = ""
    source_figure: str = ""
    modification: str = ""
    link: str = ""
    own: bool = False
    kind: str = "figure"

    @property
    def caption_html(self) -> Markup:
        return render_inline(self.caption) if self.caption else Markup("")

    @property
    def credit_line(self) -> str:
        if self.own:
            return ""
        return Figure(
            file=self.file, alt=self.alt, caption=self.caption,
            license=self.license, credit=self.credit,
            license_url=self.license_url, source_figure=self.source_figure,
            modification=self.modification,
        ).credit_line


@dataclass
class YouTube:
    """A video embed. youtube-nocookie, so a post with a video sets no cookie."""
    id: str
    caption: str = ""
    title: str = "YouTube video"
    kind: str = "youtube"

    @property
    def caption_html(self) -> Markup:
        return render_inline(self.caption) if self.caption else Markup("")


@dataclass
class Post:
    slug: str
    title: str
    date: str
    authors: list[str]
    description: str
    key_point: str
    body: list[object]
    about: str = ""
    themes: list[str] = field(default_factory=list)
    links: list[dict] = field(default_factory=list)
    needs_review: bool = False
    source_path: Path | None = None

    @property
    def url_path(self) -> str:
        return f"thinking/{self.slug}.html"

    @property
    def author_line(self) -> str:
        """Oxford-comma join, identical to Paper.author_line."""
        if len(self.authors) == 1:
            return self.authors[0]
        if len(self.authors) == 2:
            return " and ".join(self.authors)
        return ", ".join(self.authors[:-1]) + ", and " + self.authors[-1]

    @property
    def byline(self) -> str:
        return f"by {self.author_line}"

    @property
    def display_date(self) -> str:
        """'13 March 2024' — no leading zero, which strftime cannot do portably."""
        d = _dt.date.fromisoformat(self.date)
        return f"{d.day} {d.strftime('%B')} {d.year}"

    @property
    def figures(self) -> list[PostFigure]:
        return [b for b in self.body if isinstance(b, PostFigure)]


def _fence(kind: str, text: str, where: str) -> object:
    try:
        data = yaml.safe_load(text) or {}
    except (yaml.YAMLError, ValueError) as e:
        raise ContentError(f"{where}: invalid YAML in ':::{kind}' block: {e}") from e
    if not isinstance(data, dict):
        raise ContentError(f"{where}: ':::{kind}' block must be a YAML mapping")

    if kind == "figure":
        _require(data, REQUIRED_POST_FIGURE, f"{where} (figure)")
        if not data.get("own") and not (data.get("credit") and data.get("license")):
            raise ContentError(
                f"{where} (figure {data['file']}): needs 'credit' and 'license', "
                "or 'own: true' if the image is ours")
        known = {f.name for f in PostFigure.__dataclass_fields__.values()}
        unknown = set(data) - known
        if unknown:
            raise ContentError(
                f"{where} (figure {data['file']}): unknown field(s): "
                f"{', '.join(sorted(unknown))}")
        # Collapse whitespace on the one-line fields; the caption keeps its
        # Markdown intact because render_inline handles it.
        flat = {k: (v if k in ("caption", "own") else " ".join(str(v).split()))
                for k, v in data.items()}
        return PostFigure(**flat)

    if kind == "youtube":
        _require(data, ("id",), f"{where} (youtube)")
        return YouTube(id=str(data["id"]).strip(),
                       caption=data.get("caption", ""),
                       title=" ".join(str(data.get("title") or "YouTube video").split()))

    raise ContentError(f"{where}: unknown block type ':::{kind}' "
                       "(expected 'figure' or 'youtube')")


def _body_blocks(text: str, where: str) -> list[object]:
    """Split the body on ':::' fences, rendering the prose between them.

    Fences are handled before Markdown sees the text, so a figure's YAML can
    never be mangled by the Markdown parser and a figure can never arrive as a
    bare <img> without alt text.
    """
    blocks: list[object] = []
    pos = 0
    for m in FENCE_RE.finditer(text):
        prose = text[pos:m.start()].strip()
        if prose:
            blocks.append(Prose(render_markdown(prose)))
        blocks.append(_fence(m.group(1), m.group(2), where))
        pos = m.end()
    tail = text[pos:].strip()
    if tail:
        blocks.append(Prose(render_markdown(tail)))
    if not blocks:
        raise ContentError(f"{where}: post body is empty")
    return blocks


def load_post(path: Path) -> Post:
    where = str(path)
    raw = path.read_text(encoding="utf-8")
    m = FRONT_MATTER_RE.match(raw)
    if not m:
        raise ContentError(f"{where}: no YAML front matter (expected a '---' block at the top)")
    try:
        data = yaml.safe_load(m.group(1)) or {}
    except (yaml.YAMLError, ValueError) as e:
        # ValueError, not just YAMLError: PyYAML parses an unquoted date and
        # then raises ValueError constructing it, so '2020-02-31' arrives here
        # rather than as a parse error. Either way the message must name the file.
        raise ContentError(f"{where}: invalid YAML front matter: {e}") from e
    if not isinstance(data, dict):
        raise ContentError(f"{where}: front matter must be a YAML mapping")

    _require(data, REQUIRED_POST, where)

    slug = str(data["slug"]).strip()
    if not SLUG_RE.match(slug):
        raise ContentError(f"{where}: slug {slug!r} must be lowercase words joined by hyphens")
    # The filename carries the date for sorting in the directory listing; the
    # slug carries the URL. Requiring the filename to end in the slug keeps the
    # two from drifting, which would silently publish at an unexpected path.
    if not path.stem.endswith(slug):
        raise ContentError(
            f"{where}: filename should be 'YYYY-MM-DD-{slug}.md' to match slug {slug!r}")

    # An unquoted YAML date arrives as a date or datetime object, and the Jekyll
    # front matter these posts come from writes a full timestamp
    # ('2024-03-13T01:15:32+00:00'). Both normalise to the day; only the day is
    # published, so the time of day is dropped rather than rejected.
    raw_date = data["date"]
    if isinstance(raw_date, _dt.datetime):
        date = raw_date.date().isoformat()
    elif isinstance(raw_date, _dt.date):
        date = raw_date.isoformat()
    else:
        date = str(raw_date).strip()
    if not POST_DATE_RE.match(date):
        raise ContentError(f"{where}: 'date' must be YYYY-MM-DD, not {date!r}")
    try:
        _dt.date.fromisoformat(date)
    except ValueError as e:
        raise ContentError(f"{where}: 'date' is not a real date: {date!r}") from e
    if not path.stem.startswith(date):
        raise ContentError(f"{where}: filename should start with the date {date}")

    authors = data["authors"]
    if isinstance(authors, str):
        authors = [authors]
    if not isinstance(authors, list) or not all(isinstance(a, str) and a.strip() for a in authors):
        raise ContentError(f"{where}: 'authors' must be a name or a list of names")

    links = []
    for l in data.get("links", []) or []:
        if not (isinstance(l, dict) and l.get("label") and l.get("url")):
            raise ContentError(f"{where}: each 'links' entry needs a label and a url")
        links.append({"label": str(l["label"]), "url": str(l["url"])})

    known = set(REQUIRED_POST) | {"about", "themes", "links", "needs_review"}
    unknown = set(data) - known
    if unknown:
        raise ContentError(f"{where}: unknown front-matter field(s): {', '.join(sorted(unknown))}")

    return Post(
        slug=slug,
        title=" ".join(str(data["title"]).split()),
        date=date,
        authors=[a.strip() for a in authors],
        description=" ".join(str(data["description"]).split()),
        key_point=" ".join(str(data["key_point"]).split()),
        body=_body_blocks(m.group(2), where),
        about=str(data.get("about", "") or ""),
        themes=list(data.get("themes", []) or []),
        links=links,
        needs_review=bool(data.get("needs_review", False)),
        source_path=path,
    )


def sort_key(p: Post) -> tuple[str, str]:
    """Newest first. Slug breaks same-day ties so the build stays reproducible."""
    return (_negated(p.date), p.slug)


def _negated(date: str) -> str:
    """Sort an ISO date descending within an ascending sort.

    Subtracting each digit from 9 gives a string that orders the reverse of the
    original, which keeps the slug tiebreak ascending — the same reason
    model.sort_key negates its components instead of passing reverse=True.
    """
    return "".join(str(9 - int(c)) if c.isdigit() else c for c in date)


def load_posts(posts_dir: Path) -> list[Post]:
    if not posts_dir.is_dir():
        return []
    posts = sorted((load_post(p) for p in sorted(posts_dir.glob("*.md"))), key=sort_key)
    seen: dict[str, Path] = {}
    for p in posts:
        if p.slug in seen:
            raise ContentError(f"{p.source_path}: slug '{p.slug}' already used by {seen[p.slug]}")
        seen[p.slug] = p.source_path
    return posts


def validate_posts(posts: list[Post], known_papers: set[str], known_themes: set[str]) -> None:
    """Referential integrity, hard-failing like model.load_all's checks.

    A dangling `about:` would publish a link to a page that does not exist, so
    it fails the build rather than shipping a 404.
    """
    for p in posts:
        if p.about and p.about not in known_papers:
            raise ContentError(
                f"{p.source_path}: 'about' names unknown publication '{p.about}'")
        for t in p.themes:
            if t not in known_themes:
                raise ContentError(f"{p.source_path}: unknown theme '{t}'")
