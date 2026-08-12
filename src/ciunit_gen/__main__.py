"""Build the publications section: python -m ciunit_gen [--check]

--check builds nothing and only reports content problems, so it is safe to run
against a dirty tree.
"""
from __future__ import annotations

import sys
from pathlib import Path

from . import report as report_mod
from .model import ContentError, load_all
from .render import Renderer

# Hand-written pages that belong in the sitemap but are never generated.
STATIC_PAGES = [
    "index.html",
    "what-we-do.html",
    "who-we-are.html",
    "about.html",
    "climate-and-climate-impacts.html",
    "balancing-goals.html",
    "ken-caldeira.html",
    "lei-duan.html",
    "govindasamy-bala.html",
    "harry-saunders.html",
    "lamprini-papargyri.html",
    "mahendra-nimmakanti.html",
    "yuhan-wang.html",
]


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def main(argv: list[str]) -> int:
    check_only = "--check" in argv
    root = repo_root()

    try:
        papers, themes = load_all(root / "content")
    except ContentError as e:
        print(f"content error: {e}", file=sys.stderr)
        return 1

    warnings: list[str] = []

    # A missing static page in the sitemap would advertise a 404 to crawlers.
    for name in STATIC_PAGES:
        if not (root / "docs" / name).exists():
            warnings.append(f"sitemap lists {name}, which does not exist in docs/")

    for paper in papers:
        if not paper.figure:
            warnings.append(f"{paper.id}: no figure — the page will publish without one")
            continue
        fig = root / "docs" / "publications" / "figures" / paper.figure.file
        if not fig.exists():
            warnings.append(f"{paper.id}: figure file missing: docs/publications/figures/{paper.figure.file}")

    # Covers are the publications index's card images. A missing pick is normal
    # (no reprint yet); a missing file means the cover script has not been run.
    covers = root / "docs" / "publications" / "covers"
    for paper in papers:
        if not paper.thumbnail:
            warnings.append(f"{paper.id}: no cover pick — the index will draw the fallback cover")
        elif not (covers / paper.thumbnail.file).exists():
            warnings.append(
                f"{paper.id}: cover file missing: docs/publications/covers/{paper.thumbnail.file}"
                f" — run scripts/make_thumbnails.py {paper.id}")

    # docs/ is never cleaned by the build, so a renamed or deleted publication
    # would otherwise leave its cover and figure behind in git for good.
    for label, folder, wanted in (
            ("cover", covers, {p.thumbnail.file for p in papers if p.thumbnail}),
            ("figure", root / "docs" / "publications" / "figures",
             {p.figure.file for p in papers if p.figure})):
        if folder.is_dir():
            for f in sorted(folder.iterdir()):
                if f.name not in wanted:
                    warnings.append(
                        f"orphan {label} with no publication: {f.relative_to(root)}")

    for paper in papers:
        if paper.date and int(paper.date[:4]) != paper.year:
            warnings.append(
                f"{paper.id}: date {paper.date} disagrees with year {paper.year}"
                " — check which is the issue date and which is online-first")
        if paper.needs_review:
            warnings.append(f"{paper.id}: needs_review is set — claims not yet verified by an author")

    if check_only:
        print(f"{len(papers)} publication(s), {len(themes)} theme(s) — content valid.")
        for w in warnings:
            print(f"  warning: {w}")
        return 0

    if "--report" in argv:
        dest = root / "PAGES-STATUS.md"
        dest.write_text(report_mod.build(papers, themes, root), encoding="utf-8")
        print(f"wrote {dest.relative_to(root)}")
        return 0

    by_id = {p.id: p for p in papers}
    by_theme = {t.id: t for t in themes}

    r = Renderer(root)
    for paper in papers:
        r.render_paper(paper, by_theme, by_id)
    for theme in themes:
        r.render_theme(theme, [p for p in papers if theme.id in p.themes], by_id)
    r.render_index(papers, themes)
    r.render_sitemap(papers, themes, STATIC_PAGES)

    for path in r.written:
        print(f"wrote {path.relative_to(root)}")
    print(f"\n{len(papers)} publication page(s), {len(themes)} theme page(s), "
          f"{len(r.written)} file(s) total.")
    for w in warnings:
        print(f"  warning: {w}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
