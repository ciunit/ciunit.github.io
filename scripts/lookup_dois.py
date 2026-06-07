#!/usr/bin/env python3
"""Look up DOIs for the citations on ken-caldeira.html via the Crossref API.

For each citation we provide the author surnames, year, and a few distinctive
words from the page's description. We query Crossref's bibliographic search,
then score candidates by author-surname overlap and exact year match so the
best hit floats to the top for manual review.
"""
import json
import sys
import time
import urllib.parse
import urllib.request

MAILTO = "ken@ciunit.org"  # polite-pool identification for Crossref

# id, surnames, year, query terms (distinctive words from the description)
CITATIONS = [
    ("Caldeira and Rampino, 1990", ["Caldeira", "Rampino"], 1990, "carbon dioxide lifetime perturbation atmosphere ocean"),
    ("Bala et al., 2007", ["Bala", "Caldeira"], 2007, "combined climate carbon cycle biophysical effects deforestation"),
    ("Caldeira and Kasting, 1993", ["Caldeira", "Kasting"], 1993, "insensitivity global warming potential carbon dioxide emissions"),
    ("Matthews and Caldeira, 2008", ["Matthews", "Caldeira"], 2008, "stabilizing climate requires near-zero emissions"),
    ("Winkelmann et al., 2015", ["Winkelmann", "Caldeira"], 2015, "combustion available fossil fuel resources Antarctic ice sheet"),
    ("Cao et al., 2011", ["Cao", "Caldeira"], 2011, "climate response carbon dioxide solar radiation fast slow"),
    ("Cao et al., 2015", ["Cao", "Caldeira"], 2015, "climate response radiative forcing fast slow"),
    ("Rugenstein et al., 2016", ["Rugenstein", "Caldeira"], 2016, "ocean heat uptake climate sensitivity radiative forcing"),

    ("Hoffert et al., 1998", ["Hoffert"], 1998, "energy implications future stabilization atmospheric carbon dioxide"),
    ("Caldeira et al., 2003", ["Caldeira", "Jain", "Hoffert"], 2003, "climate sensitivity uncertainty carbon emissions energy stabilization"),
    ("Davis et al., 2010", ["Davis", "Caldeira", "Matthews"], 2010, "future carbon dioxide emissions existing energy infrastructure"),
    ("Tong et al., 2019", ["Tong", "Davis"], 2019, "committed emissions existing energy infrastructure 1.5 2 degree"),
    ("Davis and Caldeira, 2010", ["Davis", "Caldeira"], 2010, "consumption-based accounting carbon dioxide emissions"),
    ("Davis et al., 2011", ["Davis", "Peters", "Caldeira"], 2011, "supply chain carbon dioxide emissions extraction"),
    ("Hoffert et al., 2002", ["Hoffert"], 2002, "advanced technology paths global climate stability energy planet"),
    ("Davis et al., 2018", ["Davis", "Caldeira"], 2018, "net-zero emissions energy systems"),
    ("Shaner et al., 2018", ["Shaner", "Davis", "Caldeira"], 2018, "geophysical constraints reliability solar wind power United States"),
    ("Tong et al., 2021", ["Tong", "Caldeira"], 2021, "geophysical constraints reliable solar wind power energy storage"),
    ("Antonini et al., 2024", ["Antonini", "Caldeira"], 2024, "identifying solar wind energy reliable affordable"),

    ("Herzog et al., 2003", ["Herzog", "Caldeira"], 2003, "value temporary carbon storage"),
    ("Duan et al., 2020", ["Duan", "Caldeira"], 2020, "emissions wealthier countries mitigate greenhouse gas"),
    ("Chen and Caldeira, 2020", ["Chen", "Caldeira"], 2020, "climate change population density migration GDP"),
    ("Caldeira et al., 2023", ["Caldeira"], 2023, "green premium technology cost emissions abatement integrated assessment"),
    ("Brown et al., 2020", ["Brown", "Caldeira"], 2020, "break-even year economic return emissions abatement"),
    ("Duan et al., 2025", ["Duan", "Caldeira"], 2025, "climate adaptation rapid economic return"),

    ("Govindasamy and Caldeira, 2000", ["Govindasamy", "Caldeira"], 2000, "geoengineering climate mitigate global warming carbon dioxide"),
    ("Matthews and Caldeira, 2007", ["Matthews", "Caldeira"], 2007, "transient climate carbon simulations geoengineering termination"),
    ("Ban-Weiss and Caldeira, 2010", ["Ban-Weiss", "Caldeira"], 2010, "geoengineering optimization latitudinal distribution solar reduction"),
    ("Cao et al., 2012", ["Cao", "Caldeira"], 2012, "fast responses solar geoengineering carbon dioxide precipitation"),
    ("Pongratz et al., 2012", ["Pongratz", "Caldeira"], 2012, "crop yields solar radiation management geoengineering"),
    ("Caldeira et al., 2013", ["Caldeira", "Bala", "Cao"], 2013, "science of geoengineering"),

    ("Caldeira and Wickett, 2003", ["Caldeira", "Wickett"], 2003, "anthropogenic carbon ocean pH acidification"),
    ("Caldeira and Rampino, 1993", ["Caldeira", "Rampino"], 1993, "cretaceous carbon dioxide volcanism mass extinction"),
    ("Ricke et al., 2013", ["Ricke", "Caldeira"], 2013, "coral reefs ocean acidification aragonite saturation"),
    ("Albright et al., 2016", ["Albright", "Caldeira"], 2016, "reversal ocean acidification enhances coral reef calcification"),
    ("Albright et al., 2018", ["Albright", "Caldeira"], 2018, "carbon dioxide addition coral reef community calcification"),
    ("Duffy and Caldeira, 1997", ["Duffy", "Caldeira"], 1997, "sensitivity ocean salinity brine rejection Antarctic sea ice"),
    ("Caldeira and Duffy, 2000", ["Caldeira", "Duffy"], 2000, "Southern Ocean uptake anthropogenic carbon dioxide"),

    ("Marvel et al., 2013", ["Marvel", "Caldeira"], 2013, "geophysical limits global wind power"),
    ("Possner and Caldeira, 2017", ["Possner", "Caldeira"], 2017, "geophysical potential offshore wind power North Atlantic"),
    ("Antonini and Caldeira, 2021a", ["Antonini", "Caldeira"], 2021, "atmospheric pressure gradient limits availability wind power"),
    ("Antonini and Caldeira, 2021b", ["Antonini", "Caldeira"], 2021, "spatial constraints wind farm power production atmosphere"),

    ("Caldeira, 1992 (planktonic sulfur)", ["Caldeira"], 1992, "evolutionary pressures planktonic production atmospheric sulphur Gaia"),
    ("Caldeira and Kasting, 1992", ["Caldeira", "Kasting"], 1992, "lifespan biosphere revisited carbon dioxide"),
    ("Caldeira, 1992 (subduction carbonate)", ["Caldeira"], 1992, "enhanced Cenozoic weathering subduction pelagic carbonate degassing"),
    ("Ridgwell et al., 2003", ["Ridgwell", "Kennedy", "Caldeira"], 2003, "carbonate deposition climate stability marine plankton"),
    ("Pagani et al., 2006", ["Pagani", "Caldeira"], 2006, "Paleocene Eocene methane end-Permian climate sensitivity"),
    ("Pagani et al., 2009", ["Pagani", "Caldeira"], 2009, "high Earth-system climate sensitivity Miocene carbon dioxide plants"),
    ("Rampino and Caldeira, 1993", ["Rampino", "Caldeira"], 1993, "major episodes geologic change correlations periodicities"),
    ("Rampino and Caldeira, 2015", ["Rampino", "Caldeira"], 2015, "periodicity impacts extinctions geologic record"),
    ("Rampino et al., 2021", ["Rampino", "Caldeira"], 2021, "periodicity mass extinctions impact craters geologic record"),

    ("Tong et al., 2020", ["Tong", "Caldeira"], 2020, "battery cost storage wind solar electricity system deployment"),
    ("Duan et al., 2022", ["Duan", "Caldeira"], 2022, "value nuclear power decarbonized electricity systems"),
    ("Dowling et al., 2020", ["Dowling", "Caldeira"], 2020, "role long-duration energy storage reliable renewable electricity"),
    ("Li et al., 2024", ["Li", "Caldeira"], 2024, "long-duration short-duration energy storage wind solar"),
]


def query_crossref(terms, rows=5):
    params = {"query.bibliographic": terms, "rows": str(rows), "mailto": MAILTO}
    url = "https://api.crossref.org/works?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": f"ciunit-bio/1.0 (mailto:{MAILTO})"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)["message"]["items"]


def year_of(item):
    for k in ("published-print", "published-online", "published", "issued"):
        if k in item and item[k].get("date-parts", [[None]])[0][0]:
            return item[k]["date-parts"][0][0]
    return None


def surnames_of(item):
    return [a.get("family", "").lower() for a in item.get("author", [])]


def score(item, want_surnames, want_year):
    s = 0
    fams = surnames_of(item)
    for w in want_surnames:
        if any(w.lower() == f or w.lower() in f for f in fams):
            s += 3
    y = year_of(item)
    if y == want_year:
        s += 4
    elif y is not None and abs(y - want_year) <= 1:
        s += 1
    return s, y


results = []
for cid, surnames, year, terms in CITATIONS:
    try:
        items = query_crossref(f"{' '.join(surnames)} {terms} {year}")
    except Exception as e:
        results.append((cid, year, "ERROR", str(e), "", 0))
        time.sleep(0.5)
        continue
    ranked = sorted(items, key=lambda it: score(it, surnames, year)[0], reverse=True)
    best = ranked[0] if ranked else None
    if best:
        sc, y = score(best, surnames, year)
        title = (best.get("title") or [""])[0]
        doi = best.get("DOI", "")
        results.append((cid, year, doi, title, ",".join(surnames_of(best)), sc))
    else:
        results.append((cid, year, "NO_RESULT", "", "", 0))
    time.sleep(0.4)

print(json.dumps([
    {"id": r[0], "want_year": r[1], "doi": r[2], "title": r[3], "authors": r[4], "score": r[5]}
    for r in results
], indent=2))
