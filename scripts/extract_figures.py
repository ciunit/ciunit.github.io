#!/usr/bin/env python3
"""Extract figure images from the PDFs in pdfs/, for publication pages that need one.

Scientific figures are usually vector art, so extracting embedded raster images
finds nothing for most publications. Instead this locates each figure's caption, takes
the bounding box of the drawings and images sitting above it, and renders that
region at high resolution.

    # contact sheet of every figure in a publication, for choosing one
    python3 scripts/extract_figures.py --contact <id>

    # render one figure at full resolution into docs/publications/figures/
    python3 scripts/extract_figures.py --extract <id> --figure 3

    # which publications have a page, need a figure, and have a PDF
    python3 scripts/extract_figures.py --list

Scanned PDFs have no text layer, so there are no captions to find and the two
commands above return nothing. For those, render the pages, look at them, and
crop by eye with an explicit rectangle in PDF points:

    # page images into .figure-candidates/, for choosing a page and a crop
    python3 scripts/extract_figures.py --pages <id>
    python3 scripts/extract_figures.py --pages <id> --page 3 --dpi 150

    # render an explicit rectangle instead of a detected figure region
    python3 scripts/extract_figures.py --extract <id> --page 3 \
        --rect 54,90,545,430

Record either kind of choice in content/figure-picks.json so it can be rebuilt.

Licence is not decided here — see CLAUDE.md, "Publication pages and GEO". Record
it in the publication's YAML before the figure will render.
"""
import json
import re
import sys
from pathlib import Path

import pymupdf
import yaml

ROOT = Path(__file__).resolve().parents[1]
PDF_DIR = ROOT / "pdfs"
FIG_DIR = ROOT / "docs" / "publications" / "figures"
MAP = ROOT / "content" / "pdf-map.json"
SCRATCH = ROOT / ".figure-candidates"

CAPTION_RE = re.compile(r"^\s*(?:Fig(?:ure)?s?\.?|FIG(?:URE)?S?\.?)\s*(\d{1,2})\b", re.M)
MIN_AREA = 8000          # pt²; smaller regions are logos, rules, or stray marks


def load_map() -> dict:
    if not MAP.exists():
        sys.exit("no content/pdf-map.json — run scripts/match_pdfs.py first")
    return json.loads(MAP.read_text(encoding="utf-8"))


def papers_by_id() -> dict:
    out = {}
    for y in sorted((ROOT / "content" / "publications").glob("*.yaml")):
        d = yaml.safe_load(y.read_text(encoding="utf-8"))
        out[d["id"]] = d
    return out


def _title_score(path: Path, title: str) -> float:
    """Fraction of the title's words appearing on the PDF's first page."""
    words = {w for w in re.findall(r"[a-z]{4,}", (title or "").lower())}
    if not words:
        return 0.0
    try:
        with pymupdf.open(path) as doc:
            head = doc[0].get_text("text").lower() if doc.page_count else ""
    except Exception:  # noqa: BLE001
        return 0.0
    return sum(w in head for w in words) / len(words)


def _has_text(path: Path) -> int:
    """1 if the first two pages carry a text layer, 0 if it is an image-only scan.

    Worth a lot when choosing between copies: the figure detector locates
    captions, so a scanned copy of the same paper is useless to it even though it
    looks identical on screen."""
    try:
        with pymupdf.open(path) as doc:
            text = "".join(doc[i].get_text("text") for i in range(min(2, doc.page_count)))
    except Exception:  # noqa: BLE001
        return 0
    return 1 if len(text.strip()) > 200 else 0


def pdf_for(paper: dict, mapping: dict) -> Path | None:
    entry = mapping.get(str(paper["doi"]).lower())
    if not entry:
        return None
    files = [PDF_DIR / f for f in entry["files"] if (PDF_DIR / f).exists()]
    if not files:
        return None
    if len(files) == 1:
        return files[0]
    # Files of identical size are the same reprint saved under different names, so
    # there is nothing to choose between them — skip the comparison entirely.
    if len({f.stat().st_size for f in files}) == 1:
        return files[0]
    # Otherwise: prefer a copy with a readable text layer over an image-only scan,
    # then the one whose first page best matches this publication's own title.
    # Several PDFs can carry the same DOI because an article that *cites* it prints
    # the DOI in its reference list, and raw size is no guide — a citing article
    # with supplementary material is often the larger file.
    title = str(paper.get("title", ""))
    scored = sorted(files, key=lambda f: (_has_text(f), _title_score(f, title), f.stat().st_size))
    return scored[-1]


def find_figures(doc) -> list[dict]:
    """Locate figures as (page, caption number, region) triples."""
    figs = []
    for pno in range(doc.page_count):
        page = doc[pno]
        blocks = [b for b in page.get_text("blocks") if b[6] == 0]
        graphics = [d["rect"] for d in page.get_drawings()]
        for img in page.get_images(full=True):
            try:
                graphics.extend(page.get_image_rects(img[0]))
            except Exception:  # noqa: BLE001
                pass
        if not graphics:
            continue
        # Journal running heads, logos, and "please cite this article" banners sit
        # in the page margins and would otherwise be pulled into a figure at the
        # top of a page. Drop anything lying wholly inside the margin bands.
        head = page.rect.y0 + 0.085 * page.rect.height
        foot = page.rect.y1 - 0.05 * page.rect.height
        in_body = lambda r: not (r.y1 <= head or r.y0 >= foot)  # noqa: E731
        graphics = [g for g in graphics if in_body(g)]
        blocks = [b for b in blocks if in_body(pymupdf.Rect(b[:4]))]
        if not graphics:
            continue
        for b in blocks:
            m = CAPTION_RE.match(b[4] or "")
            if not m:
                continue
            cap = pymupdf.Rect(b[:4])
            # Graphics above the caption and belonging to its column. Requiring
            # the graphic's centre to sit within the caption's horizontal span is
            # what keeps two-column articles from dragging in the adjacent column's
            # body text; a plain overlap test is far too permissive.
            pad = max(24.0, cap.width * 0.12)
            lo, hi = cap.x0 - pad, cap.x1 + pad
            cands = sorted(
                (g for g in graphics
                 if g.y1 <= cap.y0 + 4 and g.get_area() > 4 and lo <= (g.x0 + g.x1) / 2 <= hi),
                key=lambda g: -g.y1)
            # Body text in this column, used as a ceiling.
            # Centre test, not overlap: in a two-column layout the adjacent
            # column's text reaches past the column boundary and would otherwise
            # be mistaken for a ceiling directly above the figure.
            all_texts = [pymupdf.Rect(b2[:4]) for b2 in blocks
                         if b2 is not b and len((b2[4] or "").split()) > 12]
            texts = [r for r in all_texts if lo <= (r.x0 + r.x1) / 2 <= hi]

            # Grow upward from the caption, taking only graphics contiguous with
            # what we already have. Stopping at the first intervening block of
            # body text is what prevents the crop from swallowing the previous
            # figure further up the same column.
            region, cursor = pymupdf.Rect(), cap.y0
            for g in cands:
                if g.y1 < cursor - 40:
                    break
                if any(t.y1 > g.y1 + 2 and t.y0 < cursor - 2 for t in texts):
                    break
                region |= g
                cursor = min(cursor, g.y0)
            if region.is_empty or region.get_area() < MIN_AREA:
                continue

            # Axis tick labels, units, and legends are text, not drawings, so the
            # graphics union stops short of them and the crop shears off the axes.
            # Grow the region to swallow short text sitting against it, twice, so
            # a tick label can in turn pull in the axis title beyond it.
            # Skip tall, narrow blocks: these are rotated text — journal spine
            # labels ("SUSTAINABILITY SCIENCE") and "Downloaded from ..."
            # watermarks — which sit beside figures and would be dragged in.
            short = [r for r in (pymupdf.Rect(b2[:4]) for b2 in blocks
                                 if b2 is not b and 0 < len((b2[4] or "").split()) <= 12)
                     if r.y1 <= cap.y0 + 2 and r.height <= 3 * max(r.width, 1)]
            for _ in range(2):
                near = region + (-14, -14, 14, 14)
                for r in short:
                    if r.intersects(near):
                        region |= r

            # Keep the crop near the caption's column, but generously: a figure
            # is often wider than its caption, and clipping tight to the caption
            # shears off axis labels. Other columns are already excluded by the
            # centre tests above, so this only guards against runaway unions.
            # No horizontal clip: the centre tests above already exclude the
            # adjacent column, and clipping to the caption shears the outer panels
            # off figures that are wider than their caption.
            region = region + (-6, -6, 6, 6)
            region &= page.rect
            if region.is_empty or region.get_area() < MIN_AREA:
                continue
            # Flag any body text still caught in the crop so it can be inspected.
            intruding = sum(
                1 for b2 in blocks
                if b2 is not b and len((b2[4] or "").split()) > 25
                and (pymupdf.Rect(b2[:4]) & region).get_area()
                > 0.5 * pymupdf.Rect(b2[:4]).get_area())
            figs.append({"page": pno, "num": int(m.group(1)), "rect": region,
                         "text_in_crop": intruding,
                         "caption": " ".join((b[4] or "").split())[:400]})
    # One entry per figure number, largest region wins.
    best: dict[int, dict] = {}
    for f in figs:
        if f["num"] not in best or f["rect"].get_area() > best[f["num"]]["rect"].get_area():
            best[f["num"]] = f
    return [best[k] for k in sorted(best)]


def contact(paper_id: str, papers: dict, mapping: dict) -> int:
    paper = papers[paper_id]
    path = pdf_for(paper, mapping)
    if not path:
        print(f"no PDF for {paper_id}", file=sys.stderr)
        return 1
    SCRATCH.mkdir(exist_ok=True)
    with pymupdf.open(path) as doc:
        figs = find_figures(doc)
        if not figs:
            print(f"{paper_id}: no figures detected in {path.name}", file=sys.stderr)
            return 1
        cols, thumb = 2, 380
        rows = (len(figs) + cols - 1) // cols
        out = pymupdf.open()
        pg = out.new_page(width=cols * thumb + 30, height=rows * thumb + 30)
        for i, f in enumerate(figs):
            with pymupdf.open(path) as d2:
                pix = d2[f["page"]].get_pixmap(dpi=110, clip=f["rect"])
            x, y = 15 + (i % cols) * thumb, 15 + (i // cols) * thumb
            box = pymupdf.Rect(x, y + 16, x + thumb - 10, y + thumb - 10)
            pg.insert_image(box, pixmap=pix, keep_proportion=True)
            pg.insert_text((x + 2, y + 12), f"Fig {f['num']} (p{f['page']+1})", fontsize=9)
        dest = SCRATCH / f"{paper_id}-contact.png"
        pg.get_pixmap(dpi=110).save(dest)
        out.close()
    print(f"{dest}")
    for f in figs:
        warn = "  <- BODY TEXT IN CROP" if f.get("text_in_crop") else ""
        print(f"  Fig {f['num']} p{f['page']+1}:{warn} {f['caption'][:130]}")
    return 0


def render_pages(paper_id: str, papers: dict, mapping: dict, page: int | None = None,
                 dpi: int = 110) -> int:
    """Write page images to .figure-candidates/, for PDFs the detector cannot read.

    A scan has no text layer, so find_figures() returns nothing and there is no
    caption to anchor a crop to. The only way through is to look at the pages and
    choose a rectangle by eye; this renders them so that can be done."""
    paper = papers[paper_id]
    path = pdf_for(paper, mapping)
    if not path:
        print(f"no PDF for {paper_id}", file=sys.stderr)
        return 1
    SCRATCH.mkdir(exist_ok=True)
    with pymupdf.open(path) as doc:
        pages = [page - 1] if page else range(doc.page_count)
        for i in pages:
            if not 0 <= i < doc.page_count:
                print(f"{paper_id}: no page {i + 1} (of {doc.page_count})", file=sys.stderr)
                return 1
            dest = SCRATCH / f"{paper_id}-p{i + 1}.png"
            doc[i].get_pixmap(dpi=dpi).save(dest)
            r = doc[i].rect
            print(f"{dest}  page rect 0,0,{r.x1:.0f},{r.y1:.0f} pt")
    return 0


def extract(paper_id: str, num: int, papers: dict, mapping: dict, dpi: int = 600,
            trim: dict | None = None, page: int | None = None,
            rect: list | None = None) -> int:
    """Render figure `num` of `paper_id`, or an explicit region of `page`.

    `trim` optionally removes a fraction of each side (keys left/right/top/bottom),
    for the occasional layout where a journal spine label or watermark sits inside
    the detected region as a drawing rather than as text, and so cannot be filtered
    out automatically.

    `page` (1-based) with `rect` ([x0, y0, x1, y1] in PDF points) bypasses caption
    detection entirely and renders exactly that region. That is the only route for
    a scanned PDF, and the escape hatch when the detected region shears an axis
    label off — the detector can shrink a region but never grow one."""
    paper = papers[paper_id]
    path = pdf_for(paper, mapping)
    if not path:
        print(f"no PDF for {paper_id}", file=sys.stderr)
        return 1
    with pymupdf.open(path) as doc:
        if rect:
            if not page:
                print(f"{paper_id}: --rect needs --page", file=sys.stderr)
                return 1
            if not 1 <= page <= doc.page_count:
                print(f"{paper_id}: no page {page} (of {doc.page_count})", file=sys.stderr)
                return 1
            f = {"page": page - 1, "rect": pymupdf.Rect(*rect),
                 "caption": f"(explicit crop, page {page})"}
        else:
            figs = {f["num"]: f for f in find_figures(doc)}
            if num not in figs:
                print(f"{paper_id}: no figure {num} (have {sorted(figs)})", file=sys.stderr)
                return 1
            f = figs[num]
        rect = pymupdf.Rect(f["rect"])
        if trim:
            w, h = rect.width, rect.height
            rect = pymupdf.Rect(rect.x0 + w * trim.get("left", 0),
                                rect.y0 + h * trim.get("top", 0),
                                rect.x1 - w * trim.get("right", 0),
                                rect.y1 - h * trim.get("bottom", 0))
        f = dict(f, rect=rect)
        pix = doc[f["page"]].get_pixmap(dpi=dpi, clip=rect)
        FIG_DIR.mkdir(parents=True, exist_ok=True)
        dest = FIG_DIR / f"{paper_id}.png"
        pix.save(dest)
    print(f"wrote {dest.relative_to(ROOT)}  ({pix.width}x{pix.height})")
    print(f"caption: {f['caption']}")
    return 0


def main() -> int:
    argv = sys.argv[1:]
    papers, m = papers_by_id(), load_map()["mapping"]

    if "--list" in argv:
        rows = []
        for pid, p in papers.items():
            if p.get("figure"):
                continue
            rows.append((pid, "yes" if pdf_for(p, m) else "NO PDF"))
        for pid, has in sorted(rows, key=lambda r: (r[1] != "yes", r[0])):
            print(f"  {has:6s}  {pid}")
        print(f"\n{sum(1 for _, h in rows if h == 'yes')} of {len(rows)} figureless pages have a PDF")
        return 0

    def val(flag):
        return argv[argv.index(flag) + 1] if flag in argv else None

    page = int(val("--page")) if val("--page") else None
    rect = [float(v) for v in val("--rect").split(",")] if val("--rect") else None

    if pid := val("--contact"):
        return contact(pid, papers, m)
    if pid := val("--pages"):
        return render_pages(pid, papers, m, page=page, dpi=int(val("--dpi") or 110))
    if pid := val("--extract"):
        return extract(pid, int(val("--figure") or 1), papers, m,
                       int(val("--dpi") or 600), page=page, rect=rect)
    print(__doc__)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
