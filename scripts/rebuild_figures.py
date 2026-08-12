#!/usr/bin/env python3
"""Re-extract every chosen figure and convert it for the web.

Reads content/figure-picks.json (which figure of each publication we use), extracts it
from the PDF, and writes docs/publications/figures/<id>.<ext>. Run this after changing
anything in scripts/extract_figures.py so every figure is rebuilt consistently.

A pick is one of:

    3                                        figure 3, region detected from its caption
    {"figure": 1, "trim": {"right": 0.06}}   the same, with a fraction cut off a side
    {"page": 3, "rect": [54, 90, 545, 430]}  an explicit crop in PDF points

The third form is for scans, which have no captions to detect, and for the rare
detected region that shears an axis label off — a trim can shrink a region but
never grow one.

No-derivatives publications are detected from their licence and left at native
resolution as PNG: resizing a CC BY-ND or BY-NC-ND figure would breach the
licence, so it must never depend on someone remembering to special-case it.

    python3 scripts/rebuild_figures.py           # rebuild all
    python3 scripts/rebuild_figures.py <id> ...  # rebuild specific publications
"""
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from extract_figures import extract, load_map, papers_by_id  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
FIG_DIR = ROOT / "docs" / "publications" / "figures"
PICKS = ROOT / "content" / "figure-picks.json"
CACHE = ROOT / "content" / "survey-cache.json"
LICENCES = ROOT / "content" / "thumbnail-picks.json"
MAX_WIDTH = 1600


def nd_dois() -> set[str]:
    """DOIs under a no-derivatives licence, which must not be resized.

    Read from the committed `no_derivatives` list, falling back to the survey
    cache. It used to read only the cache — which is gitignored, so on a fresh
    clone this returned an empty set and the next rebuild silently downscaled
    every CC BY-ND figure and reported success. Refusing to run beats that.
    """
    dois: set[str] = set()
    if LICENCES.exists():
        data = json.loads(LICENCES.read_text(encoding="utf-8"))
        dois |= {d.lower() for d in data.get("no_derivatives") or []}
    if CACHE.exists():
        dois |= {r["doi"].lower() for r in json.loads(CACHE.read_text(encoding="utf-8"))
                 if any("nd" in c.split("-") for c in (r.get("cc") or []))}
    if not dois:
        sys.exit(f"no no-derivatives licence data: neither {LICENCES.name} nor "
                 f"{CACHE.name} is readable. Refusing to run — resizing a CC BY-ND "
                 "figure would breach its licence.")
    return dois


def main(argv: list[str]) -> int:
    picks = {k: v for k, v in json.loads(PICKS.read_text(encoding="utf-8")).items()
             if not k.startswith("_")}
    if argv:
        picks = {k: v for k, v in picks.items() if k in argv}
        if not picks:
            print(f"no picks matched {argv}", file=sys.stderr)
            return 1

    papers, mapping, nd = papers_by_id(), load_map()["mapping"], nd_dois()
    failures = []
    for pid, spec in sorted(picks.items()):
        d = spec if isinstance(spec, dict) else {"figure": spec}
        fig, trim = d.get("figure", 1), d.get("trim")
        page, rect = d.get("page"), d.get("rect")
        paper = papers.get(pid)
        if not paper:
            failures.append(f"{pid}: no content file")
            continue
        for stale in FIG_DIR.glob(f"{pid}.*"):
            stale.unlink()
        try:
            rc = extract(pid, fig, papers, mapping, trim=trim, page=page, rect=rect)
        except Exception as e:  # noqa: BLE001
            rc, e_msg = 1, str(e)
        if rc != 0:
            failures.append(f"{pid}: extraction failed")
            continue

        png = FIG_DIR / f"{pid}.png"
        if str(paper["doi"]).lower() in nd:
            print(f"  {pid}: no-derivatives licence — kept unmodified at native size")
            continue
        out = FIG_DIR / f"{pid}.webp"
        subprocess.run(
            ["ffmpeg", "-y", "-loglevel", "error", "-i", str(png),
             "-vf", f"scale='min({MAX_WIDTH},iw)':-1:flags=lanczos", str(out)],
            check=True)
        png.unlink()

    for f in failures:
        print(f"  FAILED {f}", file=sys.stderr)
    print(f"\nrebuilt {len(picks) - len(failures)} figure(s), {len(failures)} failure(s)")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main([a for a in sys.argv[1:] if not a.startswith("-")]))
