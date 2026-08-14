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


YEAR_RE = re.compile(r"(1[89]\d\d|20\d\d)")
JOURNAL_STOPWORDS = {"of", "the", "and", "in", "for", "on", "a", "an", "to", "at"}


def journal_forms(journal: str) -> set[str]:
    """The ways a journal name plausibly appears in a filename.

    The reprint library abbreviates: `Geophysical Research Letters` is written
    `GRL`, `Nature Climate Change` as `NatureCC`, `Advances in Applied Energy` as
    `AdvApplEnergy`. Matching only the full concatenated name misses nearly every
    older file, so generate the acronym and truncated-word forms too.
    """
    parts = [w for w in re.split(r"[^a-z]+", (journal or "").lower())
             if w and w not in JOURNAL_STOPWORDS]
    if not parts:
        return set()
    forms = {"".join(parts),                                  # geophysicalresearchletters
             "".join(p[0] for p in parts),                    # grl
             "".join(p[:3] for p in parts),                   # georeslet
             "".join(p[:4] for p in parts)}                   # geopreselett
    return {f for f in forms if len(f) >= 3}


def journal_in(journal: str, alpha_stem: str) -> bool:
    """Does the filename name this journal, in full or abbreviated?"""
    return any(f in alpha_stem for f in journal_forms(journal))


def from_filename(name: str, records: list[dict]) -> str | None:
    """Match on the filename: first-author surname plus year.

    Every file in the reprint library carries both, usually as
    `<Surname>[-etal]_<Journal><Year>_<slug>.pdf` — e.g.
    `Caldeira_Nature1989_planktonic-sulphur.pdf`. That makes this the *first*
    thing to try, not a fallback: older reprints are pure image scans with no
    text layer at all, so there is no DOI and no title to read and content
    matching cannot work for exactly the papers we most want.

    Deliberately conservative. It accepts only an unambiguous match, and where
    one author has several papers in a year it requires the filename slug to
    overlap the title. An ambiguous name falls through rather than being guessed
    at, because a wrong match silently puts the wrong cover and the wrong figure
    on a page.
    """
    stem = name.rsplit(".", 1)[0]
    years = {int(y) for y in YEAR_RE.findall(stem)}
    if not years:
        return None
    words = {w for w in re.split(r"[^A-Za-z]+", stem.lower()) if len(w) > 2}
    if not words:
        return None

    alpha = re.sub(r"[^a-z]", "", stem.lower())
    hits = []
    for r in records:
        if r.get("year") not in years:
            continue
        fams = [str(a.get("family", "")).lower() for a in (r.get("authors") or [])]
        # Surnames are sometimes hyphenated in the metadata but not the filename.
        if not fams or not any(part in words for part in re.split(r"[^a-z]+", fams[0]) if part):
            continue
        title_words = {w for w in re.split(r"[^a-z0-9]+", (r.get("title") or "").lower())
                       if len(w) > 3}
        overlap = len(words & title_words)
        # Author and year alone are not enough — one author easily has several
        # papers in a year. Require the slug to corroborate, either with two
        # title words or by naming the journal.
        if overlap >= 2 or journal_in(r.get("journal"), alpha):
            hits.append((overlap, r["doi"]))
    if not hits:
        return None
    if len(hits) == 1:
        return hits[0][1]
    hits.sort(reverse=True)
    if hits[0][0] > hits[1][0]:
        return hits[0][1]
    return None


def text_supports(path: Path, title: str) -> bool:
    """Does the PDF's first page mention enough of `title` to back a filename match?

    True when there is nothing to check — no title given, or an image-only scan
    with no text layer — so this only ever *removes* matches it can disprove.
    """
    words = {w for w in re.findall(r"[a-z]{4,}", (title or "").lower())}
    if not words:
        return True
    try:
        with pymupdf.open(path) as doc:
            head = doc[0].get_text("text").lower() if doc.page_count else ""
    except Exception:  # noqa: BLE001
        return True
    if len(head.strip()) < 200:
        return True                     # image-only scan: nothing to disprove it
    return sum(w in head for w in words) / len(words) >= 0.4


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
        # ...and the same goes for filename matching, which reads `records` rather
        # than `known`. An image-only scan offers no DOI and no title text, so the
        # filename is its *only* signal; without this a new page for such a paper
        # could never find its own PDF.
        if doi not in {r["doi"] for r in records}:
            records.append({
                "doi": doi,
                "title": str(d.get("title", "")),
                "year": d.get("year"),
                "journal": str(d.get("journal", "")),
                # Crossref gives surnames in `family`; the YAML gives whole names,
                # whose last token is the surname for every author on this site.
                "authors": [{"family": str(a).split()[-1]} for a in (d.get("authors") or [])],
            })

    by_doi = {r["doi"]: r for r in records}

    mapping: dict[str, dict] = {}
    unmatched: list[str] = []
    pdfs = sorted(p for p in PDF_DIR.iterdir() if p.suffix.lower() == ".pdf")
    for i, path in enumerate(pdfs, 1):
        if i % 50 == 0:
            print(f"  ...{i}/{len(pdfs)}", file=sys.stderr)
        # Filename first: surname and year are always present, and they are the
        # only signal an image-only scan offers. Content still gets the last word
        # where it disagrees, since a printed DOI is stronger evidence than a name.
        doi = from_filename(path.name, records)
        how = "filename" if doi else ""
        by_content, how_content = dois_from_pdf(path, known)
        if by_content and by_content.startswith("TITLE:"):
            head = by_content[6:]
            by_content = next(
                (d for t, d in titles.items() if t and len(t) > 30 and t in head), None)
            how_content = "title match" if by_content else "no DOI found"
        if by_content:
            if doi and by_content != doi:
                print(f"  note: {path.name}: filename says {doi}, "
                      f"{how_content} says {by_content} — taking the latter", file=sys.stderr)
            doi, how = by_content, how_content
        elif doi and not text_supports(path, by_doi.get(doi, {}).get("title", "")):
            # A filename match that the PDF's own text contradicts. One author's
            # papers in one journal in one year look alike from the filename alone,
            # so `Caldeira-et-al_Nature1993_cooling-late-Cenozoic` was cheerfully
            # matched to the *other* Caldeira Nature 1993 letter. Where there is
            # text to check against, check it; an image-only scan is exempt,
            # because it is the case filename matching exists to serve.
            print(f"  note: {path.name}: filename says {doi}, but the first page "
                  f"does not mention that title — rejecting", file=sys.stderr)
            doi, how = None, "filename match not supported by page text"
        if not doi:
            unmatched.append(path.name)
            how = how_content
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
