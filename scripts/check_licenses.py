#!/usr/bin/env python3
"""Fetch authoritative metadata and reuse licensing for a set of DOIs.

Used when adding a paper page under content/papers/: it answers both "what
exactly is the citation?" (Crossref) and "may we reproduce a figure from it?"
(Crossref `license` + Unpaywall open-access status).

Prints a human-readable report; with --json prints machine-readable records
suitable for pasting into a content/papers/<id>.yaml stub. Like the other
scripts here it only reads — it never edits HTML or content files.

    python3 scripts/check_licenses.py                     # the pilot set
    python3 scripts/check_licenses.py 10.1038/366251a0    # specific DOIs
    python3 scripts/check_licenses.py --json > out.json
"""
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

MAILTO = "ken@ciunit.org"

# Pilot set for the papers section — spans themes and both licensing paths.
PILOT = [
    "10.1038/s41467-021-26355-z",   # Tong et al., 2021
    "10.1038/s43247-024-01260-7",   # Antonini et al., 2024
    "10.5194/esd-11-875-2020",      # Chen and Caldeira, 2020
    "10.1038/s43247-025-02579-5",   # Duan et al., 2025
    "10.1038/366251a0",             # Caldeira and Kasting, 1993
]

# Creative Commons variants that allow reproducing a figure verbatim, given
# attribution. NC/ND are listed separately because they restrict how we may use
# it (non-commercial only / no derivatives — so no recropping or restyling).
CC_FREE = {"by", "by-sa", "zero", "publicdomain", "mark"}
CC_RESTRICTED = {"by-nd", "by-nc", "by-nc-nd", "by-nc-sa"}


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": f"ciunit-gen/1.0 (mailto:{MAILTO})"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def year_of(item):
    for k in ("published-print", "published-online", "issued"):
        parts = item.get(k, {}).get("date-parts", [[None]])
        if parts and parts[0] and parts[0][0]:
            return parts[0][0]
    return None


def date_of(item):
    """ISO date if Crossref gives us one, else just the year."""
    for k in ("published-print", "published-online", "issued"):
        parts = item.get(k, {}).get("date-parts", [[None]])
        if parts and parts[0] and parts[0][0]:
            return "-".join(f"{p:02d}" if i else str(p) for i, p in enumerate(parts[0]))
    return None


def crossref(doi):
    item = get("https://api.crossref.org/works/" + urllib.parse.quote(doi))["message"]
    authors = [
        {"given": a.get("given", ""), "family": a.get("family", "")}
        for a in item.get("author", [])
    ]
    licenses = sorted({lic.get("URL", "") for lic in item.get("license", [])})
    return {
        "doi": item.get("DOI", doi),
        "title": (item.get("title") or [""])[0],
        "journal": (item.get("container-title") or [""])[0],
        "publisher": item.get("publisher", ""),
        "year": year_of(item),
        "date": date_of(item),
        "volume": item.get("volume", ""),
        "pages": item.get("page", ""),
        "authors": authors,
        "licenses": licenses,
        "abstract": item.get("abstract", ""),
    }


def unpaywall(doi):
    url = f"https://api.unpaywall.org/v2/{urllib.parse.quote(doi)}?email={MAILTO}"
    try:
        data = get(url)
    except urllib.error.HTTPError as e:
        return {"error": f"HTTP {e.code}"}
    best = data.get("best_oa_location") or {}
    return {
        "is_oa": data.get("is_oa"),
        "oa_status": data.get("oa_status"),
        "oa_license": best.get("license"),
        "oa_url": best.get("url_for_landing_page") or best.get("url"),
    }


def cc_codes(rec):
    """Creative Commons codes (e.g. 'by', 'by-nc-nd') implied by the metadata.

    Crossref also lists non-reuse licenses such as Springer's text-and-data-mining
    terms (springer.com/tdm); those grant nothing here and are ignored.
    """
    codes = set()
    for url in rec["licenses"]:
        low = url.lower().rstrip("/")
        for marker in ("creativecommons.org/licenses/", "creativecommons.org/publicdomain/"):
            if marker in low:
                codes.add(low.split(marker, 1)[1].split("/")[0])
    oa_lic = (rec["oa"].get("oa_license") or "").lower()
    if oa_lic.startswith("cc-"):
        codes.add(oa_lic[3:])
    elif oa_lic in ("cc0", "public-domain"):
        codes.add("zero")
    return codes


def figure_verdict(rec):
    """How may we source a figure from this paper?"""
    codes = cc_codes(rec)
    if codes & CC_FREE:
        return f"CC {sorted(codes & CC_FREE)[0].upper()} — reproduce with attribution"
    restricted = sorted(codes & CC_RESTRICTED)
    if restricted:
        code = restricted[0].upper()
        note = "unmodified only" if "ND" in code else "non-commercial only"
        return f"CC {code} — reproduce with attribution, {note}"
    if codes:
        return f"CC {sorted(codes)[0].upper()} — check terms"
    return "Not openly licensed — rely on author reuse-on-own-website rights"


def main():
    argv = [a for a in sys.argv[1:] if not a.startswith("--")]
    as_json = "--json" in sys.argv
    dois = argv or PILOT

    records = []
    for doi in dois:
        try:
            rec = crossref(doi)
        except Exception as e:  # noqa: BLE001 — report and continue
            records.append({"doi": doi, "error": str(e)})
            print(f"[{doi}] ERROR {e}", file=sys.stderr)
            time.sleep(0.4)
            continue
        time.sleep(0.4)
        rec["oa"] = unpaywall(doi)
        rec["figure_verdict"] = figure_verdict(rec)
        records.append(rec)
        time.sleep(0.4)

    if as_json:
        json.dump(records, sys.stdout, indent=2)
        return

    for rec in records:
        if "error" in rec:
            print(f"\n{rec['doi']}\n  ERROR: {rec['error']}")
            continue
        who = ", ".join(f"{a['family']}" for a in rec["authors"][:4])
        if len(rec["authors"]) > 4:
            who += " et al."
        print(f"\n{rec['doi']}")
        print(f"  {who} ({rec['year']})")
        print(f"  {rec['title']}")
        print(f"  {rec['journal']} {rec['volume']} {rec['pages']} — {rec['publisher']}")
        print(f"  crossref licenses: {rec['licenses'] or 'none listed'}")
        print(f"  unpaywall: {rec['oa']}")
        print(f"  FIGURE: {rec['figure_verdict']}")


if __name__ == "__main__":
    main()
