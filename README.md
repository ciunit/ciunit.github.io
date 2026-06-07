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
│   └── css/
│       └── style.css      #   shared stylesheet for all pages
│
├── scripts/               # Python helpers (run locally; not part of the site)
│   ├── lookup_dois.py     #   find DOIs for bio-page citations via Crossref
│   └── verify_dois.py     #   verify candidate DOIs / re-search ambiguous ones
│
└── README.md
```

Each page is standalone HTML that shares the same header navigation and footer.
There is no templating layer yet — when adding a page, copy the header/footer
from an existing page so the nav stays consistent.

### Planned: content generator

A Python generator (e.g. `src/ciunit_gen/` driven by templates + a `content/`
directory of Markdown/YAML) is **planned but not yet built**. When it exists it
will write into `docs/`, and that output will be committed like everything else.

## Scripts

The `scripts/` helpers support maintaining the citation links on
`docs/ken-caldeira.html`. They query the free [Crossref API](https://www.crossref.org/documentation/retrieve-metadata/rest-api/)
(no key required) and print results for review — they do **not** edit the HTML.

```bash
python3 scripts/lookup_dois.py    # best-guess DOI per citation, with a match score
python3 scripts/verify_dois.py    # confirm specific DOIs and re-search hard cases
```

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
