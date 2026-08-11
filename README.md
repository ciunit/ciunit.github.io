# ciunit.github.io

Source repository for **[CIunit.org](https://ciunit.org)**, the public-facing
website of the **Conceptual Investigations Unit** — a research consortium,
closely affiliated with the Stanford University Sustainable Solutions Lab,
that develops conceptual frameworks, quantitative analyses, and
interdisciplinary investigations at the intersection of climate, energy,
technology, and society.

The site is **static HTML/CSS**, served by GitHub Pages. Some content is
prepared with **Python tooling** in this repository and committed into the
published `docs/` directory.

## How it works

GitHub Pages serves the site from the **`/docs` folder on the `main` branch**.
There is no server-side build step: whatever HTML/CSS/assets are committed under
`docs/` is exactly what gets published. Any Python tooling runs **locally** and
its output is committed to git.

```
ciunit.github.io/
├── docs/                  # PUBLISHED SITE — this is what GitHub Pages serves
│   ├── CNAME              #   custom domain (ciunit.org)
│   ├── index.html         #   landing page
│   ├── about.html         #   "What is CIunit.org?"
│   ├── what-we-do.html
│   ├── who-we-are.html
│   ├── ken-caldeira.html  #   bio page (linked from who-we-are.html)
│   ├── publications.html  #   GENERATED — index of the publications section
│   ├── publications/      #   GENERATED — one page per publication
│   │   ├── <id>.html
│   │   └── figures/       #   figure images (licence recorded in content/)
│   ├── topics/            #   GENERATED — theme reference pages
│   ├── sitemap.xml        #   GENERATED
│   ├── robots.txt
│   └── css/
│       └── style.css      #   shared stylesheet for all pages
│
├── content/               # SOURCE OF TRUTH for the publications section
│   ├── publications/      #   one file per publication, <id>.yaml
│   └── themes.yaml        #   theme pages
│
├── src/ciunit_gen/        # the generator (see below)
│
├── scripts/               # Python helpers (run locally; not part of the site)
│   ├── lookup_dois.py     #   find DOIs for bio-page citations via Crossref
│   ├── verify_dois.py     #   verify candidate DOIs / re-search ambiguous ones
│   └── check_licenses.py  #   metadata + figure-reuse licence for a DOI
│
├── requirements.txt
└── README.md
```

Hand-written pages are standalone HTML sharing the same header navigation and
footer — when adding one, copy the header/footer from an existing page so the nav
stays consistent. Pages under `docs/publications/` and `docs/topics/` are **generated**;
edit the YAML in `content/` instead and rebuild.

## Content generator

The publications section is generated from `content/` into `docs/`. GitHub Pages runs no
build step, so **the generated HTML is committed** like everything else.

```bash
pip install -r requirements.txt
PYTHONPATH=src python -m ciunit_gen --check   # validate content, write nothing
PYTHONPATH=src python -m ciunit_gen           # write docs/publications/, docs/topics/,
                                              # docs/publications.html, docs/sitemap.xml
```

The build is reproducible: running it twice leaves the tree unchanged. It refuses
to generate a page whose content file is missing a key finding, a figure licence,
or figure alt text, and warns about publications flagged `needs_review`. It never
touches the hand-written pages — the `What We Publish` nav link in those is
maintained by hand.

See `CLAUDE.md` ("Publication pages and GEO") for the writing conventions these pages
follow and why.

## Scripts

The `scripts/` helpers support maintaining the citation links on
`docs/ken-caldeira.html`. They query the free [Crossref API](https://www.crossref.org/documentation/retrieve-metadata/rest-api/)
(no key required) and print results for review — they do **not** edit the HTML.

```bash
python3 scripts/lookup_dois.py       # best-guess DOI per citation, with a match score
python3 scripts/verify_dois.py       # confirm specific DOIs and re-search hard cases
python3 scripts/check_licenses.py    # citation metadata + whether a figure may be reused
```

`check_licenses.py` is the one to run before adding a figure to a publication page:
it resolves the DOI against Crossref and Unpaywall and reports whether the article
is
CC-BY (reproduce with attribution), CC BY-NC-ND (reproduce **unmodified** only), or
not openly licensed (rely on author reuse rights).

## Preview locally

No tooling needed to view the static site:

```bash
python -m http.server -d docs 8000
# open http://localhost:8000
```

## Deploying

Commit changes under `docs/` and push to `main`; GitHub Pages publishes
automatically (allow a minute or two — watch the repo's **Actions** tab).

- **Custom domain:** `ciunit.org`, set via `docs/CNAME`.
- **Pages source:** `main` branch, `/docs` folder (Repo → Settings → Pages).
  Changing this setting requires **admin** on the repo — see `CLAUDE.md`.

## Analytics

Traffic is measured with **Cloudflare Web Analytics** (cookieless, privacy-
friendly — no consent banner needed). The beacon snippet lives in the `<head>`
of every page under `docs/`.

- **View the dashboard:** sign in at <https://dash.cloudflare.com/> → **Analytics
  & Logs → Web Analytics**.
- **Account:** Cloudflare, under **ken@CIunit.org**.
- Data only reflects visits to the live site (`ciunit.org`), not local previews,
  and can take up to an hour to appear after the first visits.

## Accounts & administration

- **CIunit.org email addresses** (e.g. `ken@CIunit.org`, `lei@CIunit.org`,
  `harry@CIunit.org`) are managed in **Google Workspace** at
  <https://workspace.google.com/dashboard>.
- **GitHub:** the repo lives under the <https://github.com/ciunit> account,
  whose admin login is **ken@CIunit.org**.
