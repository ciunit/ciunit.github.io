# CLAUDE.md

Guidance for Claude Code working in this repository. See `README.md` for the
human-facing overview.

## What this is

Static website for the **Conceptual Investigations Unit**, published at
**ciunit.org** via GitHub Pages. Plain HTML/CSS today; a Python content
generator is planned but not yet built.

## Publishing model — read this first

- GitHub Pages serves the site from the **`/docs` folder on `main`**. There is
  **no build step**: the committed contents of `docs/` are exactly what ships.
- Edit the live site by editing the HTML/CSS under `docs/`.
- **Changes go live only when committed and pushed.** Edits in the working tree
  do not appear on ciunit.org until then.

## Working agreements

- **The user commits and pushes themselves.** Do not offer to commit/push or do
  it unprompted. Make the edits and stop.
- After edits, the user can preview with `python -m http.server -d docs 8000`.

## Admin gotcha (cost us real time once)

- The repo is owned by a **separate personal account, `ciunit`**.
- The working/local account is **`KCaldeira`**, which has **push but NOT admin**
  (it's a collaborator; personal-repo collaborators cannot be granted admin).
- Therefore **GitHub Pages settings cannot be changed via `gh`** with the local
  credentials — `gh api ... PUT .../pages` returns 404 (permission, not
  missing). Changing the Pages source/custom domain requires signing into the
  web UI as the **`ciunit`** account. Don't burn time retrying the API.

## Conventions

- **Naming:** use **"CIunit.org"** only for the website/domain/email
  (`ken@CIunit.org`). The organization itself is **"Conceptual Investigations
  Unit"** everywhere else (titles, logo, prose).
- **Page structure:** every page is standalone HTML sharing an identical header
  `<nav>` and `<footer>`, with styling in `docs/css/style.css`. When adding a
  page, copy the header/footer from an existing page and add any new nav link to
  **all** pages. There is no shared include/template yet.
- **Analytics:** every page's `<head>` carries the same Cloudflare Web Analytics
  beacon (`static.cloudflareinsights.com/beacon.min.js`, cookieless — no consent
  banner needed). A new page must include it too; copy the snippet from an
  existing page's `<head>`.
- **Custom domain:** lives in `docs/CNAME` (`ciunit.org`). It must stay inside
  the published folder (`docs/`), or Pages drops the custom domain.
- **People cards are alphabetical by last name:** on `who-we-are.html`, order the
  member cards (and the Affiliates cards) alphabetically by surname — e.g.
  Caldeira, Davis, Duan. Insert any new person into the correct alphabetical slot.
- **Non-linked cards are visually distinct:** any card that is *not* a clickable
  link gets the `card-static` class, giving it a slightly darker background
  (`--bg-dark`) than the page. This covers both not-yet-linked placeholders (e.g.
  the Affiliates cards on `who-we-are.html`) and permanent non-link content cards
  (e.g. the "Why conceptual investigations?" card on `about.html`). Clickable
  cards instead use `card-link` (an `<a>`) and keep the lighter default
  background. When a placeholder gains a link, convert the `<div>` to
  `<a class="card person card-link" href="…">` and drop `card-static`.
- **Oxford comma:** use the serial comma in lists of three or more — "climate,
  energy, and society", not "climate, energy and society". (Standard for the
  site's academic register.) This applies to the series itself; a two-item pair
  inside one list element, e.g. "the economics of mitigation and adaptation",
  takes no comma.
- **External links open in a new tab:** any link going *off* the `ciunit.org`
  domain gets `target="_blank" rel="noopener noreferrer"`. Internal (relative)
  links and `mailto:` links do **not**. Apply this to every new external link you
  add. In practice all `href="http…"` links in this repo are external (internal
  links are relative), so the rule is: `href="http…"` ⇒ add target + rel.

## Citations on bio pages (`docs/ken-caldeira.html`, `docs/lei-duan.html`)

- Each citation links to the paper via **`https://doi.org/<doi>`** (resolves to
  the publisher's site). Keep this form for consistency even if given a direct
  publisher URL.
- **Within each "Selected scientific contributions" subsection, bullets are
  ordered most-recent-first.** A bullet with multiple references is ranked by its
  *newest* citation year. When adding a paper, insert it at the correct
  chronological slot (newest at the top of its `<h3>` group).
- `scripts/lookup_dois.py` and `scripts/verify_dois.py` query the Crossref API
  to find/verify DOIs. They print candidates for review; they don't edit HTML.
  Verify author + year + title before trusting an auto-matched DOI.

## Paper pages and GEO (`docs/papers/`, `docs/topics/`)

The papers section is written to be **found, understood, and cited by AI answer
engines** (generative-engine / answer-engine optimization), not only to rank in
search. That goal, not ordinary SEO, decides how these pages are structured.

**These pages are generated — never hand-edit them.** Source of truth is
`content/papers/<id>.yaml` and `content/themes.yaml`; run `python -m ciunit_gen`
(see README) and commit its output. Every generated file carries a `GENERATED`
banner comment.

Content rules:

- **State the claim; don't make a reader reconstruct it.** Every paper page opens
  with one self-contained `key_finding` sentence carrying the number — "models
  underestimate 22-year maximum monthly high-temperature anomalies by 11–12%",
  not "we found significant biases". It must make sense quoted in isolation, with
  no pronouns or antecedents pointing back into the page.
- **Headings are questions people actually ask** — "What question did this paper
  ask?", "Does climate change affect economic growth?" — not "Introduction" or
  "Results".
- **Answer sits above evidence.** Order is question → short answer → evidence and
  qualifications → sources. Both humans and retrieval systems get the short answer
  without reading to the bottom.
- **Provenance is the point.** Authors, affiliation, date, DOI, and links to data
  and code carry more weight here than any keyword tuning.
- **Prefer few authoritative pages over many thin ones.** A paper page with no
  real result and no figure is worse than no page. Theme pages under
  `docs/topics/` are the citable units; paper pages are the evidence beneath them.
- **Scientific claims are the user's to approve.** Ground every number in the
  paper's abstract or text. If a claim can't be verified from an accessible
  source, set `needs_review: true` in the YAML and flag it — the generator will
  list those files.

Mechanics:

- Every page carries `<meta name="description">`, `<link rel="canonical">` to the
  `https://ciunit.org/…` URL, and JSON-LD. Paper pages use `WebPage` with a
  `mainEntity` `ScholarlyArticle` keyed by DOI.
- **Figures:** `figure.credit` and `figure.license` are required data fields, so
  captions are generated, never hand-typed. Use `scripts/check_licenses.py` to
  determine reuse rights before adding a figure. CC-BY reproduces freely with
  attribution; CC BY-NC-ND requires the image be used **unmodified** (no
  recropping or restyling); non-open papers rely on author reuse-on-own-website
  rights. Alt text is required and must describe what the figure *shows* — it is
  read by retrieval systems, which cannot see the image.
- `docs/sitemap.xml` and `docs/robots.txt` are part of this; regenerate the
  sitemap whenever pages are added.

## Secrets

- Never commit tokens/credentials. `.gitignore` blocks `*token*`, `*.secret`,
  `.env`. If a token is ever exposed (e.g. pasted/screenshotted), treat it as
  compromised and have the user revoke it immediately.
