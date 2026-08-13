#!/usr/bin/env python3
"""Match PDFs in pdfs/ to the DOIs cited on the site.

The PDF collection is a personal reprint library, far larger than the set of
publications on the site and named inconsistently, so matching is done on content
rather than filename: the DOI printed on the article, falling back to the title.

    python3 scripts/match_pdfs.py            # report coverage
    python3 scripts/match_pdfs.py --json     # machine-readable mapping

Writes content/pdf-map.json when run without --json. Read-only with respect to
the PDFs themselves.
"""
import json
import re
import sys
from pathlib import Path

import pymupdf
import yaml

ROOT = Path(__file__).resolve().parents[1]
PDF_DIR = ROOT / "pdfs"
CACHE = ROOT / "content" / "survey-cache.json"
OUT = ROOT / "content" / "pdf-map.json"

# A DOI as printed on a paper. Deliberately not greedy about trailing
# punctuation, which is routinely glued on by the surrounding sentence.
DOI_RE = re.compile(r"\b(10\.\d{4,9}/[^\s\"'<>,;()\[\]]+)", re.I)
TRAILING = ".,;:)]}>'\"-–—"


def clean_doi(doi: str) -> str:
    return doi.rstrip(TRAILING).lower()


def norm_title(t: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (t or "").lower()).strip()


def dois_from_pdf(path: Path, known: set[str]) -> tuple[str | None, str]:
    """Return (doi, how). Looks at metadata first, then the first two pages.

    Only DOIs we already know about are accepted, which neatly avoids the main
    failure mode — picking up the DOI of a cited reference instead of the
    article's own.
    """
    try:
        doc = pymupdf.open(path)
    except Exception as e:  # noqa: BLE001
        return None, f"unreadable ({e.__class__.__name__})"

    with doc:
        meta = " ".join(str(v) for v in (doc.metadata or {}).values() if v)
        for cand in DOI_RE.findall(meta):
            if clean_doi(cand) in known:
                return clean_doi(cand), "metadata"

        text = ""
        for i in range(min(2, doc.page_count)):
            try:
                text += doc[i].get_text("text")
            except Exception:  # noqa: BLE001
                break
        for cand in DOI_RE.findall(text):
            if clean_doi(cand) in known:
                return clean_doi(cand), "page text"

        # Fall back to matching the title, for older scans with no printed DOI.
        head = norm_title(text[:1800])
        if head:
            return ("TITLE:" + head), "title text"
    return None, "no DOI found"


def main() -> int:
    if not PDF_DIR.is_dir():
        print(f"no {PDF_DIR}", file=sys.stderr)
        return 1
    records = json.loads(CACHE.read_text(encoding="utf-8")) if CACHE.exists() else []
    known = {r["doi"] for r in records}
    titles = {norm_title(r.get("title", "")): r["doi"] for r in records if r.get("title")}

    built = {}
    for y in sorted((ROOT / "content" / "publications").glob("*.yaml")):
        d = yaml.safe_load(y.read_text(encoding="utf-8"))
        doi = str(d["doi"]).lower()
        built[doi] = {"id": d["id"], "has_figure": bool(d.get("figure"))}
        # A publication with a page is cited on the site by definition. Taking the
        # known set from the survey cache alone made a freshly written page
        # unmatchable until the (slow, networked) survey was re-run — so a new page
        # could not get its cover or figure in the same sitting.
        known.add(doi)
        titles.setdefault(norm_title(str(d.get("title", ""))), doi)

    mapping: dict[str, dict] = {}
    unmatched: list[str] = []
    pdfs = sorted(p for p in PDF_DIR.iterdir() if p.suffix.lower() == ".pdf")
    for i, path in enumerate(pdfs, 1):
        if i % 50 == 0:
            print(f"  ...{i}/{len(pdfs)}", file=sys.stderr)
        doi, how = dois_from_pdf(path, known)
        if doi and doi.startswith("TITLE:"):
            head = doi[6:]
            doi = next((d for t, d in titles.items() if t and len(t) > 30 and t in head), None)
            how = "title match" if doi else "no DOI found"
        if not doi:
            unmatched.append(path.name)
            continue
        # Prefer the first PDF found for a DOI; note duplicates.
        entry = mapping.setdefault(doi, {"files": [], "how": how})
        entry["files"].append(path.name)

    for doi, entry in mapping.items():
        entry.update(built.get(doi, {}))

    matched_dois = set(mapping)
    need_fig = {d for d, v in built.items() if not v["has_figure"]}
    print(f"\nPDFs scanned            : {len(pdfs)}")
    print(f"matched to a cited DOI  : {sum(len(v['files']) for v in mapping.values())} "
          f"file(s) -> {len(matched_dois)} distinct publication(s)")
    print(f"unmatched               : {len(unmatched)}")
    print()
    print(f"publications with a page : {len(built)}")
    print(f"  ...of which need a figure : {len(need_fig)}")
    print(f"  ...and now have a PDF     : {len(need_fig & matched_dois)}")
    print(f"cited publications with no page but a PDF : "
          f"{len(matched_dois - set(built))}")

    if "--json" in sys.argv:
        json.dump({"mapping": mapping, "unmatched": unmatched}, sys.stdout, indent=1)
    else:
        OUT.write_text(json.dumps({"mapping": mapping, "unmatched": unmatched},
                                  indent=1), encoding="utf-8")
        print(f"\nwrote {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
