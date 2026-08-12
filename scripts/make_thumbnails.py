#!/usr/bin/env python3
"""Render each publication's own first page as the cover shown on the index.

The publications index is a grid of covers; this makes them. Source of truth for
*which* page is content/thumbnail-picks.json, because page 1 is not always the
article's first page — Science reprints and IOP downloads put a publisher cover
sheet ahead of it, and that is an editorial judgement that has to be recorded
rather than re-derived.

    python3 scripts/make_thumbnails.py --audit       # which PDFs look like cover sheets
    python3 scripts/make_thumbnails.py --contact     # one sheet of every cover, to eyeball
    python3 scripts/make_thumbnails.py --contact <id>   # first pages of one PDF, larger
    python3 scripts/make_thumbnails.py               # build every cover in the picks file
    python3 scripts/make_thumbnails.py <id> ...      # rebuild specific publications
    python3 scripts/make_thumbnails.py --prune       # delete covers with no pick

Covers go in docs/publications/covers/, NOT in figures/. Two reasons, both of
which bite silently: extract_figures.extract() hard-codes its output to
figures/<id>.png, and rebuild_figures.py sweeps figures/<id>.* before every
rebuild — so a cover living there would be deleted by the next figure rebuild
with no error anywhere.

Reuse basis is recorded once in the picks file rather than per publication: every
publication in this collection has a CIunit author, so the basis is identical for
all of them. See CLAUDE.md, "Publication pages and GEO".
"""
import json
import subprocess
import sys
from pathlib import Path

import pymupdf

sys.path.insert(0, str(Path(__file__).resolve().parent))
from extract_figures import load_map, papers_by_id, pdf_for  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
COVER_DIR = ROOT / "docs" / "publications" / "covers"
PICKS = ROOT / "content" / "thumbnail-picks.json"
SCRATCH = ROOT / ".figure-candidates"

WIDTH = 400              # px; cover scale — recognisable, body text not readable
QUALITY = 80             # libwebp; ffmpeg's default of 75 is soft on dense text
SUPERSAMPLE = 3          # render large then downscale: text aliases badly otherwise
TARGET_AR = 3 / 4        # every cover the same shape, so <img> can carry width/height

# Phrases that only appear on a publisher's download cover sheet, never on an
# article's own first page.
COVER_MARKS = ("to cite this article", "personal, non-commercial",
               "this copy is for your personal", "downloaded from")


def load_picks() -> tuple[dict, dict]:
    if not PICKS.exists():
        return {}, {}
    data = json.loads(PICKS.read_text(encoding="utf-8"))
    picks = {}
    for pid, spec in (data.get("picks") or {}).items():
        picks[pid] = spec if isinstance(spec, dict) else {"page": spec}
    return picks, data


def page_of(pid: str, picks: dict) -> int:
    return int(picks.get(pid, {}).get("page", 1))


def cover_sheet_score(page) -> tuple[int, list[str]]:
    """Word count and marker hits for a page, to flag publisher cover sheets.

    Proposes, never decides: several first pages are legitimately sparse because
    they carry a graphical abstract, and those make the best covers of all.
    """
    text = page.get_text("text")
    low = text.lower()
    return len(text.split()), [m for m in COVER_MARKS if m in low]


def audit(papers: dict, mapping: dict, picks: dict) -> int:
    rows = []
    for pid in sorted(papers):
        path = pdf_for(papers[pid], mapping)
        if not path:
            continue
        with pymupdf.open(path) as doc:
            words, hits = cover_sheet_score(doc[0])
            rows.append((words, pid, hits, doc.page_count))
    print(f"{'words':>6}  {'pages':>5}  {'pick':>4}  publication")
    print(f"{'-' * 6}  {'-' * 5}  {'-' * 4}  {'-' * 44}")
    for words, pid, hits, n in sorted(rows):
        flag = "  <- COVER SHEET? " + ", ".join(hits) if hits else ""
        print(f"{words:6d}  {n:5d}  {page_of(pid, picks):4d}  {pid}{flag}")
    print(f"\n{len(rows)} PDFs. Low word count alone is not proof — a graphical "
          "abstract is sparse too.\nLook at --contact before recording a pick.")
    return 0


def contact(papers: dict, mapping: dict, picks: dict, only: str | None) -> int:
    SCRATCH.mkdir(exist_ok=True)
    if only:
        # One publication, its first few pages, big enough to read the masthead.
        path = pdf_for(papers[only], mapping)
        if not path:
            print(f"no PDF for {only}", file=sys.stderr)
            return 1
        with pymupdf.open(path) as doc:
            n = min(4, doc.page_count)
            cols, thumb = 4, 360
            out = pymupdf.open()
            pg = out.new_page(width=cols * thumb + 20, height=thumb + 30)
            for i in range(n):
                pix = doc[i].get_pixmap(dpi=110)
                x = 10 + i * thumb
                pg.insert_image(pymupdf.Rect(x, 26, x + thumb - 10, thumb + 20),
                                pixmap=pix, keep_proportion=True)
                mark = " (picked)" if i + 1 == page_of(only, picks) else ""
                pg.insert_text((x + 2, 20), f"p{i + 1}{mark}", fontsize=10)
            dest = SCRATCH / f"{only}-cover-contact.png"
            pg.get_pixmap(dpi=110).save(dest)
        print(dest)
        return 0

    ids = [p for p in sorted(papers) if pdf_for(papers[p], mapping)]
    cols, thumb = 6, 190
    rows = (len(ids) + cols - 1) // cols
    out = pymupdf.open()
    pg = out.new_page(width=cols * thumb + 20, height=rows * (thumb + 22) + 20)
    for i, pid in enumerate(ids):
        path = pdf_for(papers[pid], mapping)
        page_no = page_of(pid, picks)
        with pymupdf.open(path) as doc:
            page_no = min(page_no, doc.page_count)
            pix = doc[page_no - 1].get_pixmap(dpi=72)
        x, y = 10 + (i % cols) * thumb, 10 + (i // cols) * (thumb + 22)
        pg.insert_image(pymupdf.Rect(x, y + 14, x + thumb - 8, y + thumb + 10),
                        pixmap=pix, keep_proportion=True)
        pg.insert_text((x + 2, y + 10), f"{pid[:26]} p{page_no}", fontsize=6)
    dest = SCRATCH / "covers-contact.png"
    pg.get_pixmap(dpi=110).save(dest)
    out.close()
    print(f"{dest}  ({len(ids)} covers)")
    return 0


def render_cover(pdf: Path, page_no: int, width: int, quality: int, dest: Path) -> tuple[int, int]:
    """Render `page_no` cropped to a constant 3:4 from the top, and write WebP.

    Cropping at render time rather than with CSS object-fit is what lets every
    <img> carry the same width/height, which is what keeps a 57-image page from
    shifting as it loads.
    """
    with pymupdf.open(pdf) as doc:
        page = doc[page_no - 1]
        r = page.rect
        if r.width / r.height < TARGET_AR:          # taller than 3:4 — trim the foot
            clip = pymupdf.Rect(r.x0, r.y0, r.x1, r.y0 + r.width / TARGET_AR)
        else:                                       # wider — trim the outer margin
            clip = pymupdf.Rect(r.x0, r.y0, r.x0 + r.height * TARGET_AR, r.y1)
        zoom = (width * SUPERSAMPLE) / clip.width
        pix = page.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom), clip=clip)
    tmp = dest.with_suffix(".png")
    dest.parent.mkdir(parents=True, exist_ok=True)
    pix.save(tmp)
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-i", str(tmp),
         "-vf", f"scale={width}:-1:flags=lanczos", "-quality", str(quality), str(dest)],
        check=True)
    tmp.unlink()
    return width, round(width / TARGET_AR)


def orphans(picks: dict) -> list[Path]:
    """Covers whose publication or pick is gone. The build never cleans docs/."""
    if not COVER_DIR.is_dir():
        return []
    wanted = {f"{pid}.webp" for pid in picks}
    return [f for f in sorted(COVER_DIR.iterdir()) if f.name not in wanted]


def main(argv: list[str]) -> int:
    papers, mapping = papers_by_id(), load_map()["mapping"]
    picks, _raw = load_picks()

    flags = [a for a in argv if a.startswith("--")]
    ids = [a for a in argv if not a.startswith("--")]

    def val(flag, default):
        return int(argv[argv.index(flag) + 1]) if flag in argv else default

    if "--audit" in flags:
        return audit(papers, mapping, picks)
    if "--contact" in flags:
        return contact(papers, mapping, picks, ids[0] if ids else None)
    if "--prune" in flags:
        gone = orphans(picks)
        for f in gone:
            f.unlink()
            print(f"removed {f.relative_to(ROOT)}")
        print(f"pruned {len(gone)} cover(s)")
        return 0

    width, quality = val("--width", WIDTH), val("--quality", QUALITY)
    todo = ids or sorted(picks)
    if not todo:
        print("no picks in content/thumbnail-picks.json — run --audit and --contact first",
              file=sys.stderr)
        return 1

    failures = []
    for pid in todo:
        if pid not in picks:
            failures.append(f"{pid}: no pick in {PICKS.name}")
            continue
        if pid not in papers:
            failures.append(f"{pid}: no content file")
            continue
        path = pdf_for(papers[pid], mapping)
        if not path:
            failures.append(f"{pid}: no PDF")
            continue
        for stale in COVER_DIR.glob(f"{pid}.*"):
            stale.unlink()
        dest = COVER_DIR / f"{pid}.webp"
        try:
            w, h = render_cover(path, page_of(pid, picks), width, quality, dest)
        except Exception as e:  # noqa: BLE001
            failures.append(f"{pid}: {e}")
            continue
        kb = round(dest.stat().st_size / 1024)
        print(f"wrote {dest.relative_to(ROOT)}  ({w}x{h}, {kb} KB, page {page_of(pid, picks)})")

    for f in orphans(picks):
        print(f"  orphan cover with no pick: {f.relative_to(ROOT)}  (--prune removes it)")
    for f in failures:
        print(f"  FAILED {f}", file=sys.stderr)
    print(f"\nbuilt {len(todo) - len(failures)} cover(s), {len(failures)} failure(s)")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
