#!/usr/bin/env python3
"""Verify candidate DOIs (by direct Crossref lookup) and re-search the
ambiguous citations that the first pass got wrong."""
import json
import time
import urllib.parse
import urllib.request

MAILTO = "ken@ciunit.org"

# Candidate DOIs I believe are correct — confirm title/authors/year.
VERIFY = {
    "Cao et al., 2011": "10.1029/2011GL046713",
    "Rugenstein et al., 2016": "10.1002/2016GL070907",
    "Davis et al., 2018 (Science net-zero)": "10.1126/science.aas9793",
    "Pagani et al., 2006": "10.1126/science.1136110",
    "Pagani et al., 2009": "10.1038/nature08133",
    "Rampino and Caldeira, 2015": "10.1093/mnras/stv2088",
    "Rampino et al., 2021 (primary)": "10.1080/08912963.2020.1849178",
    "Caldeira sulfur (1989?)": "10.1038/337732a0",
}

# Ambiguous — re-search with sharper terms.
SEARCH = {
    "Duan et al., 2020 (wealthier countries)": "Duan Caldeira inequality wealthy countries climate mitigation emissions 2020",
    "Li et al., 2024 (storage, w/ Caldeira)": "Li Caldeira long-duration short-duration energy storage solar wind 2024",
}


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": f"ciunit-bio/1.0 (mailto:{MAILTO})"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def fmt(item):
    title = (item.get("title") or [""])[0]
    fams = ",".join(a.get("family", "") for a in item.get("author", []))
    y = None
    for k in ("published-print", "published-online", "issued"):
        if k in item and item[k].get("date-parts", [[None]])[0][0]:
            y = item[k]["date-parts"][0][0]
            break
    return f"{item.get('DOI','')} | {y} | {fams} | {title}"


print("=== VERIFY candidate DOIs ===")
for label, doi in VERIFY.items():
    try:
        item = get("https://api.crossref.org/works/" + urllib.parse.quote(doi))["message"]
        print(f"\n[{label}]\n  {fmt(item)}")
    except Exception as e:
        print(f"\n[{label}] DOI {doi} -> ERROR {e}")
    time.sleep(0.4)

print("\n\n=== SEARCH ambiguous ===")
for label, q in SEARCH.items():
    print(f"\n[{label}] query: {q}")
    try:
        params = {"query.bibliographic": q, "rows": "6", "mailto": MAILTO}
        items = get("https://api.crossref.org/works?" + urllib.parse.urlencode(params))["message"]["items"]
        for it in items:
            print("  - " + fmt(it))
    except Exception as e:
        print(f"  ERROR {e}")
    time.sleep(0.4)
