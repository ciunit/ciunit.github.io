#!/usr/bin/env python3
"""Re-extract every chosen figure and convert it for the web.

Reads content/figure-picks.json (which figure of each paper we use), extracts it
from the PDF, and writes docs/papers/figures/<id>.<ext>. Run this after changing
anything in scripts/extract_figures.py so every figure is rebuilt consistently.

No-derivatives papers are detected from their licence and left at native
resolution as PNG: resizing a CC BY-ND or BY-NC-ND figure would breach the
licence, so it must never depend on someone remembering to special-case it.

    python3 scripts/rebuild_figures.py           # rebuild all
    python3 scripts/rebuild_figures.py <id> ...  # rebuild specific papers
"""
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from extract_figures import extract, load_map, papers_by_id  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
FIG_DIR = ROOT / "docs" / "papers" / "figures"
PICKS = ROOT / "content" / "figure-picks.json"
CACHE = ROOT / "content" / "survey-cache.json"
MAX_WIDTH = 1600


def nd_dois() -> set[str]:
    """DOIs under a no-derivatives licence, which must not be resized."""
    if not CACHE.exists():
        return set()
    return {r["doi"] for r in json.loads(CACHE.read_text(encoding="utf-8"))
            if any("nd" in c.split("-") for c in (r.get("cc") or []))}


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
        fig = spec["figure"] if isinstance(spec, dict) else spec
        trim = spec.get("trim") if isinstance(spec, dict) else None
        paper = papers.get(pid)
        if not paper:
            failures.append(f"{pid}: no content file")
            continue
        for stale in FIG_DIR.glob(f"{pid}.*"):
            stale.unlink()
        try:
            rc = extract(pid, fig, papers, mapping, trim=trim)
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
