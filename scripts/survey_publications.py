#!/usr/bin/env python3
"""Survey every DOI cited on the site: metadata, abstract availability, figure licence.

Answers the question "which publications do we have enough material to write a
page for?" before any page is written. A publication page needs a verifiable key
finding,
which in practice means an accessible abstract; and a figure needs a licence we
can act on. This reports both, per DOI.

Writes a JSON cache so the (slow, network-bound) survey is run once and reused:

    python3 scripts/survey_papers.py                  # survey, write cache + report
    python3 scripts/survey_papers.py --from-cache     # re-render report from cache
    python3 scripts/survey_papers.py --markdown       # emit the status document

Read-only with respect to the site: it never edits HTML or content files.
"""
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_licenses import cc_codes, crossref, figure_verdict, unpaywall  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
CACHE = ROOT / "content" / "survey-cache.json"
MAILTO = "ken@ciunit.org"

# Pages whose citations we survey. The generated publications section is skipped —
# its DOIs come from content/publications/ and are already accounted for.
SKIP_PAGES = {"index.html", "publications.html", "about.html", "what-we-do.html", "who-we-are.html"}


def site_dois() -> dict[str, list[str]]:
    """Every DOI cited on a hand-written page, mapped to the pages citing it."""
    found: dict[str, list[str]] = {}
    for page in sorted(DOCS.glob("*.html")):
        if page.name in SKIP_PAGES:
            continue
        for doi in re.findall(r'href="https://doi\.org/([^"]+)"', page.read_text(encoding="utf-8")):
            found.setdefault(doi.lower().rstrip("."), []).append(page.name)
    return found


def built_dois() -> dict[str, str]:
    """DOIs that already have a page, mapped to their content id."""
    import yaml
    out = {}
    for y in sorted((ROOT / "content" / "publications").glob("*.yaml")):
        data = yaml.safe_load(y.read_text(encoding="utf-8"))
        out[str(data["doi"]).lower()] = data["id"]
    return out


def clean_abstract(raw: str) -> str:
    """Crossref abstracts are JATS XML fragments; strip to plain text."""
    import html as _html
    text = re.sub(r"<[^>]+>", " ", raw or "")
    text = _html.unescape(text)
    text = re.sub(r"^\s*Abstract\b[.:]?\s*", "", text, flags=re.I)
    return " ".join(text.split())


def semantic_scholar(doi: str) -> dict:
    """Fallback abstract source. Rate-limited, so back off on 429."""
    url = ("https://api.semanticscholar.org/graph/v1/paper/DOI:"
           + urllib.parse.quote(doi) + "?fields=abstract,openAccessPdf")
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": f"ciunit-gen/1.0 (mailto:{MAILTO})"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.load(resp)
        except urllib.error.HTTPError as e:
            if e.code == 429:
                time.sleep(5 * (attempt + 1))
                continue
            return {}
        except Exception:  # noqa: BLE001
            return {}
    return {}


def survey() -> list[dict]:
    cites = site_dois()
    built = built_dois()
    records = []
    total = len(cites)
    for i, (doi, pages) in enumerate(sorted(cites.items()), 1):
        print(f"  [{i:3d}/{total}] {doi}", file=sys.stderr)
        rec: dict = {"doi": doi, "cited_on": sorted(set(pages)), "built_as": built.get(doi)}
        try:
            rec.update(crossref(doi))
        except Exception as e:  # noqa: BLE001
            rec["error"] = str(e)
            records.append(rec)
            time.sleep(0.4)
            continue
        time.sleep(0.4)

        rec["oa"] = unpaywall(doi)
        time.sleep(0.4)

        abstract = clean_abstract(rec.pop("abstract", "") or "")
        rec["abstract_source"] = "crossref" if len(abstract) > 120 else None
        if not rec["abstract_source"]:
            s2 = semantic_scholar(doi)
            s2_abs = (s2.get("abstract") or "").strip()
            if len(s2_abs) > 120:
                abstract = " ".join(s2_abs.split())
                rec["abstract_source"] = "semantic-scholar"
            rec["oa_pdf"] = (s2.get("openAccessPdf") or {}).get("url") or None
            time.sleep(0.4)
        rec["abstract"] = abstract
        rec["figure_verdict"] = figure_verdict(rec)
        rec["cc"] = sorted(cc_codes(rec))
        records.append(rec)
    return records


# DOI prefixes whose figure images we can actually fetch, verified by probing:
# Springer Nature and Springer serve figures from media.springernature.com and
# Copernicus from <journal>.copernicus.org, both of which return 200. Everything
# else tested refuses automated access — IOP redirects to a bot wall
# (validate.perfdrive.com), Wiley/AGU and PNAS return 403, and Elsevier serves a
# gated linkinghub page. An open licence is therefore NOT sufficient: 15 IOP
# articles here are CC-BY but still unreachable.
FIG_HOSTS = {"10.1038", "10.5194", "10.1007"}


def figure_source(rec: dict) -> str:
    if not rec.get("cc"):
        return "author reuse"
    return "retrievable" if rec["doi"].split("/")[0] in FIG_HOSTS else "author reuse (licensed, host blocks us)"


def tier(rec: dict) -> str:
    """How much of a page can we responsibly write for this publication?"""
    if rec.get("error"):
        return "metadata-failed"
    if rec.get("built_as"):
        return "has-page"
    if not rec.get("abstract_source"):
        return "blocked-no-abstract"
    return "ready-with-figure" if figure_source(rec) == "retrievable" else "ready-needs-figure"


TIER_NOTE = {
    "has-page": "Already published as a publication page.",
    "ready-with-figure": "Abstract reachable and figure retrievable — a complete page needs no input from you.",
    "ready-needs-figure": "Abstract reachable, but the figure must be supplied by an author.",
    "blocked-no-abstract": "No abstract reachable anywhere — a verifiable key finding cannot be written without the publication itself.",
    "metadata-failed": "Crossref lookup failed — the DOI may be wrong.",
}
TIER_ORDER = ["has-page", "ready-with-figure", "ready-needs-figure",
              "blocked-no-abstract", "metadata-failed"]


def short_cite(rec: dict) -> str:
    authors = rec.get("authors") or []
    if not authors:
        return rec["doi"]
    fam = [a.get("family", "") for a in authors]
    who = fam[0] if len(fam) == 1 else (
        f"{fam[0]} and {fam[1]}" if len(fam) == 2 else f"{fam[0]} et al.")
    return f"{who}, {rec.get('year')}"


def report(records: list[dict]) -> None:
    from collections import Counter
    c = Counter(tier(r) for r in records)
    print("\nSurveyed", len(records), "DOI(s)\n")
    for k in TIER_ORDER:
        if c[k]:
            print(f"  {c[k]:3d}  {k:20s} {TIER_NOTE[k]}")


def markdown(records: list[dict]) -> str:
    from collections import Counter
    c = Counter(tier(r) for r in records)
    lines = [
        "# Publication page status",
        "",
        "Generated by `python3 scripts/survey_publications.py --markdown` — do not edit by hand.",
        "One row per DOI cited anywhere on ciunit.org.",
        "",
        "A publication page is only worth publishing if it states a **verifiable key finding**",
        "(see `CLAUDE.md`, \"Publication pages and GEO\"). In practice that means we need a",
        "reachable abstract. A figure additionally needs both an open licence *and* a",
        "publisher that permits automated access — those are not the same thing.",
        "",
        f"- **{len(records)}** distinct DOIs cited on the site",
        f"- **{c['has-page']}** already have a page",
        f"- **{c['ready-with-figure'] + c['ready-needs-figure']}** could have one written now",
        f"- **{c['blocked-no-abstract']}** are blocked pending the publication itself",
        "",
        "| Tier | Count | Meaning |",
        "| --- | ---: | --- |",
    ]
    for k in TIER_ORDER:
        if c[k]:
            lines.append(f"| `{k}` | {c[k]} | {TIER_NOTE[k]} |")

    lines += ["", "## Publications", "",
              "Ordered by tier, then newest first.", "",
              "| Citation | Title | Journal | Tier | Figure | Abstract | Cited on |",
              "| --- | --- | --- | --- | --- | --- | --- |"]
    for rec in sorted(records, key=lambda r: (TIER_ORDER.index(tier(r)), -(r.get("year") or 0))):
        title = (rec.get("title") or "").replace("|", "\\|")
        fig = "—" if rec.get("error") else figure_source(rec)
        if rec.get("built_as"):
            fig = f"page `{rec['built_as']}`"
        pages = ", ".join(p.replace(".html", "") for p in rec.get("cited_on", []))
        lines.append(
            f"| [{short_cite(rec)}](https://doi.org/{rec['doi']}) | {title[:120]} "
            f"| {rec.get('journal', '')[:32]} | `{tier(rec)}` | {fig} "
            f"| {rec.get('abstract_source') or '**none**'} | <sub>{pages}</sub> |")
    return "\n".join(lines) + "\n"


def main() -> int:
    if "--from-cache" in sys.argv or "--markdown" in sys.argv:
        if not CACHE.exists():
            print(f"no cache at {CACHE}; run without --from-cache first", file=sys.stderr)
            return 1
        records = json.loads(CACHE.read_text(encoding="utf-8"))
        # Which publications have a page is the one thing that changes without the
        # network, so re-derive it from disk rather than trusting the cache —
        # otherwise the status document silently under-reports what is done.
        built = built_dois()
        for rec in records:
            rec["built_as"] = built.get(rec["doi"])
    else:
        records = survey()
        CACHE.parent.mkdir(parents=True, exist_ok=True)
        CACHE.write_text(json.dumps(records, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"\ncached -> {CACHE.relative_to(ROOT)}", file=sys.stderr)

    if "--markdown" in sys.argv:
        print(markdown(records))
    else:
        report(records)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
