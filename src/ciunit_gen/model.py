"""Content model for the publications section.

Loads `content/publications/*.yaml` and `content/themes.yaml` into validated objects.
Validation is deliberately strict about the fields that make a page worth citing
(see CLAUDE.md, "Publication pages and GEO"): a page missing its key finding, or a
figure missing its licence or alt text, is a page that quietly degrades into
noise, so we refuse to generate it rather than ship it.
"""
from __future__ import annotations

import datetime as _dt
import json
import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml


class ContentError(Exception):
    """A content file is missing or malformed. Message names the file."""


# 'YYYY', 'YYYY-MM' or 'YYYY-MM-DD'. Anchored at both ends so 'March 2024' and
# '2024-3' are rejected rather than silently sorting as though undated.
DATE_RE = re.compile(r"(\d{4})(?:-(\d{2})(?:-(\d{2}))?)?$")


# Fields every publication must carry for its page to be worth publishing.
# 'themes' is optional: a publication with no theme yet still gets a page, and
# lands under "Other publications" on the index rather than blocking the build.
REQUIRED_PAPER = ("id", "doi", "title", "authors", "journal", "year",
                  "description", "question", "key_finding", "findings", "matters")
REQUIRED_FIGURE = ("file", "alt", "caption", "license", "credit")
REQUIRED_THEME = ("id", "title", "question", "short_answer", "description")


def _require(data: dict, keys, where: str) -> None:
    missing = [k for k in keys if not data.get(k)]
    if missing:
        raise ContentError(f"{where}: missing required field(s): {', '.join(missing)}")


def _paragraphs(value, where: str, field_name: str) -> list[str]:
    """Prose fields are a list of plain-text paragraphs.

    Plain text, not HTML: everything is autoescaped at render time, so content
    files can never inject markup into the published site. Cross-references go
    through the structured `related`/`links`/`evidence` fields instead.
    """
    if isinstance(value, str):
        value = [value]
    if not isinstance(value, list) or not all(isinstance(p, str) for p in value):
        raise ContentError(f"{where}: '{field_name}' must be a string or list of strings")
    out = [" ".join(p.split()) for p in value if p.strip()]
    if not out:
        raise ContentError(f"{where}: '{field_name}' is empty")
    return out


@dataclass
class Figure:
    file: str
    alt: str
    caption: str
    license: str
    credit: str
    license_url: str = ""
    source_figure: str = ""
    source_url: str = ""
    modification: str = ""
    # Where the image came from — "publisher website", "PDF (300 dpi)", etc.
    # Recorded so PAGES-STATUS.md can show why a figure is low resolution.
    source: str = ""

    @property
    def credit_line(self) -> str:
        """Full attribution sentence, assembled from recorded facts.

        Never hand-typed in a content file — that is how a wrong licence ends up
        under a figure.
        """
        bits = []
        if self.source_figure:
            bits.append(f"{self.source_figure} from {self.credit}")
        else:
            bits.append(self.credit)
        bits.append(f"Reproduced under {self.license}")
        if self.modification:
            bits.append(self.modification)
        return ". ".join(b.rstrip(".") for b in bits) + "."


@dataclass
class Link:
    label: str
    url: str


@dataclass
class Thumbnail:
    """Cover image for the publications index — the publication's own first page.

    Derived rather than authored, which is why this lives in
    content/thumbnail-picks.json and not in each publication's YAML. The licence
    basis is identical for every one of them, so per-publication blocks would be
    49 chances to drift; the only editorial fact is *which* page is the article's
    real first page, since a Science reprint or an IOP download puts a publisher
    cover sheet ahead of it.

    There is deliberately no alt text. The cover sits inside a link whose text
    already reads "<title> — Albright et al., 2016 · Nature", so it ships
    alt="" and describing it would make a screen reader announce the same
    publication twice.
    """
    file: str
    page: int = 1
    license: str = ""
    note: str = ""


@dataclass
class Paper:
    id: str
    doi: str
    title: str
    authors: list[str]
    journal: str
    year: int
    themes: list[str]
    description: str
    question: list[str]
    key_finding: str
    findings: list[str]
    matters: list[str]
    date: str = ""
    volume: str = ""
    pages: str = ""
    figure: Figure | None = None
    thumbnail: Thumbnail | None = None
    links: list[Link] = field(default_factory=list)
    related: list[str] = field(default_factory=list)
    needs_review: bool = False
    source_path: Path | None = None

    @property
    def url_path(self) -> str:
        return f"publications/{self.id}.html"

    @property
    def doi_url(self) -> str:
        return f"https://doi.org/{self.doi}"

    @property
    def author_line(self) -> str:
        if len(self.authors) == 1:
            return self.authors[0]
        if len(self.authors) == 2:
            return " and ".join(self.authors)
        return ", ".join(self.authors[:-1]) + ", and " + self.authors[-1]

    @property
    def short_citation(self) -> str:
        """e.g. 'Tong et al., 2021' — matches the style used on the bio pages."""
        first = self.authors[0].split()[-1] if self.authors else ""
        if len(self.authors) == 1:
            who = first
        elif len(self.authors) == 2:
            who = f"{first} and {self.authors[1].split()[-1]}"
        else:
            who = f"{first} et al."
        return f"{who}, {self.year}"

    @property
    def search_text(self) -> str:
        """Lower-cased haystack for the index's client-side filter.

        Carries the author list and the one-sentence description, neither of
        which is printed on the card. The index no longer shows the key finding,
        so without them a search for a co-author or a topic word would find
        nothing at all.

        Theme ids are included because they are readable slugs, so searching
        "ocean acidification" matches every publication on that theme and not
        just the one whose title happens to contain both words.
        """
        return " ".join([self.title, self.journal, str(self.year),
                         *self.authors, *self.themes, self.description]).lower()

    @property
    def full_citation(self) -> str:
        bits = [f"{self.author_line} ({self.year}). {self.title.rstrip('.')}. {self.journal}"]
        if self.volume:
            bits.append(f" {self.volume}")
        if self.pages:
            bits.append(f", {self.pages}")
        return "".join(bits) + "."


@dataclass
class Evidence:
    """A claim on a theme page, attributed to one of our papers."""
    claim: str
    paper: str


@dataclass
class Theme:
    id: str
    title: str
    question: str
    short_answer: str
    description: str
    why_it_matters: list[str] = field(default_factory=list)
    evidence: list[Evidence] = field(default_factory=list)
    methods: list[str] = field(default_factory=list)

    @property
    def url_path(self) -> str:
        return f"topics/{self.id}.html"


def load_paper(path: Path) -> Paper:
    where = str(path)
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as e:
        raise ContentError(f"{where}: invalid YAML: {e}") from e
    if not isinstance(data, dict):
        raise ContentError(f"{where}: expected a YAML mapping")

    _require(data, REQUIRED_PAPER, where)
    if data["id"] != path.stem:
        raise ContentError(f"{where}: id '{data['id']}' does not match filename '{path.stem}'")

    figure = None
    if data.get("figure"):
        fig = data["figure"]
        if not isinstance(fig, dict):
            raise ContentError(f"{where}: 'figure' must be a mapping")
        _require(fig, REQUIRED_FIGURE, f"{where} (figure)")
        # Collapse whitespace: YAML folded scalars ('>') leave a trailing newline,
        # which would otherwise end up inside alt text and the credit line.
        figure = Figure(**{k: " ".join(str(v).split())
                           for k, v in fig.items() if k in Figure.__annotations__})

    links = [Link(label=l["label"], url=l["url"]) for l in data.get("links", []) or []]

    # A malformed date leaves the index's sort key undefined, so refuse it rather
    # than silently filing the publication under its year alone.
    date = str(data.get("date", "") or "")
    if date and not DATE_RE.match(date):
        raise ContentError(
            f"{where}: 'date' must be YYYY, YYYY-MM or YYYY-MM-DD, not {date!r}")

    return Paper(
        id=data["id"],
        doi=str(data["doi"]).strip(),
        title=" ".join(str(data["title"]).split()),
        authors=list(data["authors"]),
        journal=str(data["journal"]),
        year=int(data["year"]),
        themes=list(data.get("themes", []) or []),
        description=" ".join(str(data["description"]).split()),
        question=_paragraphs(data["question"], where, "question"),
        key_finding=" ".join(str(data["key_finding"]).split()),
        findings=_paragraphs(data["findings"], where, "findings"),
        matters=_paragraphs(data["matters"], where, "matters"),
        date=date,
        volume=str(data.get("volume", "") or ""),
        pages=str(data.get("pages", "") or ""),
        figure=figure,
        links=links,
        related=list(data.get("related", []) or []),
        needs_review=bool(data.get("needs_review", False)),
        source_path=path,
    )


def sort_key(p: Paper) -> tuple[int, int, int, str]:
    """Newest first across mixed date precision, as one total order.

    Most publications carry a bare year, a few a full date. A missing month
    sorts to the *end* of its year rather than to a guessed midpoint: something
    we know only the year of should not displace something we know came out in
    December. `id` breaks the remaining ties so the build stays reproducible.

    Each component is negated rather than passing reverse=True, which would
    reverse the id tiebreak too.
    """
    m = DATE_RE.match(p.date or "")
    if not m:
        return (-p.year, 0, 0, p.id)
    y, mo, d = m.groups()
    return (-int(y), -int(mo or 0), -int(d or 0), p.id)


def load_thumbnails(path: Path, known: set[str]) -> dict[str, Thumbnail]:
    """Cover picks for the publications index, from content/thumbnail-picks.json.

    See Thumbnail for why these are not per-publication YAML blocks. A pick is
    either a bare page number or a mapping, mirroring content/figure-picks.json.
    """
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise ContentError(f"{path}: invalid JSON: {e}") from e

    basis = data.get("basis") or {}
    out = {}
    for pid, spec in (data.get("picks") or {}).items():
        if pid not in known:
            raise ContentError(f"{path}: pick for unknown publication '{pid}'")
        d = spec if isinstance(spec, dict) else {"page": spec}
        out[pid] = Thumbnail(
            file=str(d.get("file") or f"{pid}.webp"),
            page=int(d.get("page", 1)),
            license=str(d.get("license") or basis.get("license", "")),
            note=str(d.get("note", "")),
        )
    return out


def load_themes(path: Path) -> list[Theme]:
    where = str(path)
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or []
    if not isinstance(data, list):
        raise ContentError(f"{where}: expected a YAML list of themes")
    themes = []
    for entry in data:
        _require(entry, REQUIRED_THEME, where)
        themes.append(Theme(
            id=entry["id"],
            title=entry["title"],
            question=" ".join(str(entry["question"]).split()),
            short_answer=" ".join(str(entry["short_answer"]).split()),
            description=" ".join(str(entry["description"]).split()),
            why_it_matters=_paragraphs(entry.get("why_it_matters", []) or [""], where, "why_it_matters")
            if entry.get("why_it_matters") else [],
            evidence=[Evidence(claim=" ".join(e["claim"].split()), paper=e["paper"])
                      for e in entry.get("evidence", []) or []],
            methods=_paragraphs(entry["methods"], where, "methods") if entry.get("methods") else [],
        ))
    return themes


def load_all(content_dir: Path) -> tuple[list[Paper], list[Theme]]:
    papers_dir = content_dir / "publications"
    if not papers_dir.is_dir():
        raise ContentError(f"{papers_dir}: no papers directory")
    papers = sorted((load_paper(p) for p in sorted(papers_dir.glob("*.yaml"))),
                    key=sort_key)

    themes_file = content_dir / "themes.yaml"
    themes = load_themes(themes_file) if themes_file.exists() else []

    known_papers = {p.id for p in papers}
    known_themes = {t.id for t in themes}
    for p in papers:
        for t in p.themes:
            if t not in known_themes:
                raise ContentError(f"{p.source_path}: unknown theme '{t}'")
        for r in p.related:
            if r not in known_papers:
                raise ContentError(f"{p.source_path}: 'related' points at unknown publication '{r}'")
    for t in themes:
        for e in t.evidence:
            if e.paper not in known_papers:
                raise ContentError(f"themes.yaml ({t.id}): evidence cites unknown publication '{e.paper}'")

    thumbs = load_thumbnails(content_dir / "thumbnail-picks.json", known_papers)
    for p in papers:
        p.thumbnail = thumbs.get(p.id)
    return papers, themes


def today() -> str:
    return _dt.date.today().isoformat()
