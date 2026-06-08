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
- **Custom domain:** lives in `docs/CNAME` (`ciunit.org`). It must stay inside
  the published folder (`docs/`), or Pages drops the custom domain.
- **External links open in a new tab:** any link going *off* the `ciunit.org`
  domain gets `target="_blank" rel="noopener noreferrer"`. Internal (relative)
  links and `mailto:` links do **not**. Apply this to every new external link you
  add. In practice all `href="http…"` links in this repo are external (internal
  links are relative), so the rule is: `href="http…"` ⇒ add target + rel.

## Citations on bio pages (`docs/ken-caldeira.html`)

- Each citation links to the paper via **`https://doi.org/<doi>`** (resolves to
  the publisher's site). Keep this form for consistency even if given a direct
  publisher URL.
- `scripts/lookup_dois.py` and `scripts/verify_dois.py` query the Crossref API
  to find/verify DOIs. They print candidates for review; they don't edit HTML.
  Verify author + year + title before trusting an auto-matched DOI.

## Secrets

- Never commit tokens/credentials. `.gitignore` blocks `*token*`, `*.secret`,
  `.env`. If a token is ever exposed (e.g. pasted/screenshotted), treat it as
  compromised and have the user revoke it immediately.
