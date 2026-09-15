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
  **all** pages. There is no shared include for the hand-written pages, so a new
  nav item means two jobs: one edit to
  `src/ciunit_gen/templates/_base.html.j2`, which covers every generated page,
  and the same edit by hand in each of the 13 hand-written `docs/*.html` files.
  Nothing in `--check` catches a page whose nav went stale; verify with
  `grep -L 'href=".*<new-page>"' docs/*.html`.
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

- **Each citation links to that publication's own page** — `publications/<id>.html`,
  a relative link, so no `target`/`rel`. Every citation on both bio pages has a page
  and is linked this way; the publication page carries the DOI onward to the
  publisher. A citation whose publication has no page yet keeps the
  **`https://doi.org/<doi>`** form (with `target`/`rel`, being external) until one
  exists. Never link to a publisher URL directly.
- **Within each "Selected scientific contributions" subsection, bullets are
  ordered most-recent-first.** A bullet with multiple references is ranked by its
  *newest* citation year. When adding a publication, insert it at the correct
  chronological slot (newest at the top of its `<h3>` group).
- `scripts/lookup_dois.py` and `scripts/verify_dois.py` query the Crossref API
  to find/verify DOIs. They print candidates for review; they don't edit HTML.
  Verify author + year + title before trusting an auto-matched DOI.

## Publication pages and GEO (`docs/publications/`, `docs/topics/`)

The publications section is written to be **found, understood, and cited by AI answer
engines** (generative-engine / answer-engine optimization), not only to rank in
search. That goal, not ordinary SEO, decides how these pages are structured.

**If `CONTINUE-HERE.md` exists, read it first** — it records the decisions
already made and the next tasks, and is deleted once that work is done.

**Read `PUBLICATION-PAGES.md` before adding or changing a publication page.** It is the full
procedure — schema, commands, figure extraction, licensing, verification, and the
list of what is still outstanding. This section covers only *why* the pages are
written the way they are.

**These pages are generated — never hand-edit them.** Source of truth is
`content/publications/<id>.yaml` and `content/themes.yaml`; run `python -m ciunit_gen`
(see README) and commit its output. Every generated file carries a `GENERATED`
banner comment.

Three things that have caused real errors and are easy to repeat:

- **A plain YAML scalar cannot contain `": "`.** Any paragraph with a colon
  followed by a space must be a `- >` block scalar. Run `--check` after editing.
- **Several PDFs can carry the same DOI**, because a citing article prints it in its
  references. Figure extraction picks by title match, not file size.
- **An open licence does not imply a reachable figure.** IOP articles here are CC BY
  but the site blocks automated access; and CC BY-NC-ND figures must not be
  resized.

Content rules:

- **State the claim; don't make a reader reconstruct it.** Every publication page opens
  with one self-contained `key_finding` sentence carrying the number — "models
  underestimate 22-year maximum monthly high-temperature anomalies by 11–12%",
  not "we found significant biases". It must make sense quoted in isolation, with
  no pronouns or antecedents pointing back into the page.
- **Headings are questions people actually ask** — "What question did this
  research address?", "Does climate change affect economic growth?" — not "Introduction" or
  "Results".
- **Answer sits above evidence.** Order is question → short answer → evidence and
  qualifications → sources. Both humans and retrieval systems get the short answer
  without reading to the bottom.
- **Provenance is the point.** Authors, affiliation, date, DOI, and links to data
  and code carry more weight here than any keyword tuning.
- **Prefer few authoritative pages over many thin ones.** A publication page with no
  real result and no figure is worse than no page. Theme pages under
  `docs/topics/` are the citable units; publication pages are the evidence beneath
  them.
- **Scientific claims are the user's to approve.** Ground every number in the
  publication's abstract or text. If a claim can't be verified from an accessible
  source, set `needs_review: true` in the YAML and flag it — the generator will
  list those files.

Mechanics:

- Every page carries `<meta name="description">`, `<link rel="canonical">` to the
  `https://ciunit.org/…` URL, and JSON-LD. Publication pages use `WebPage` with a
  `mainEntity` `ScholarlyArticle` keyed by DOI.
- **Figures:** `figure.credit` and `figure.license` are required data fields, so
  captions are generated, never hand-typed. Use `scripts/check_licenses.py` to
  determine reuse rights before adding a figure. CC-BY reproduces freely with
  attribution; CC BY-NC-ND requires the image be used **unmodified** (no
  recropping or restyling); non-open articles rely on author reuse-on-own-website
  rights. Alt text is required and must describe what the figure *shows* — it is
  read by retrieval systems, which cannot see the image. **This rule is about
  `figure`, the evidence image on a publication page.** The index's cover images
  are a separate thing and deliberately ship `alt=""`; see "Cover images" in
  `PUBLICATION-PAGES.md` before "fixing" that.
- **The index is a cover grid, newest first** — one box per publication showing
  its own first page, the whole box a link. It is also the only page linking to
  `docs/topics/`, via the theme strip under the lede; don't remove that without
  giving the theme pages another route in from the nav.
- `docs/sitemap.xml` and `docs/robots.txt` are part of this; regenerate the
  sitemap whenever pages are added.
- **The reprint library on Google Drive**, readable by anyone with the link:
  <https://drive.google.com/drive/folders/1PEDfXnofnxgMm9IzANzGMWBjkQBi2auk?usp=sharing>
  It mirrors the gitignored `pdfs/` folder, filename for filename. **Any publication
  that might be paywalled gets a `Copy` link to its PDF there** in
  `PAYWALL-STATUS.md` — that means every `closed` and `green` row, and every
  `bronze` row too, since `bronze` only means the publisher currently serves the
  article free without granting a licence and can stop at any time. `gold` and
  `hybrid` are open under a Creative Commons licence and need no copy. Find a file's
  id by searching the folder for the exact filename `scripts/extract_figures.py`
  picks from `pdfs/`, and check the Drive copy's byte size against the local one
  before recording the link.

## What We Are Thinking (`docs/thinking/`, `docs/what-we-are-thinking.html`)

Posts: walk-throughs of our own papers, and commentary on questions of climate,
energy, and how research works. The section exists because the strongest of these
were written on Ken's personal blog at kencaldeira.com and belong next to the
publication pages they discuss; `~/kcaldeira.github.io/CIUNIT-HANDOFF.md`
classifies all 72 posts there and is the migration checklist.

**These pages are generated — never hand-edit them.** Source of truth is
`content/posts/YYYY-MM-DD-<slug>.md`; run `python -m ciunit_gen` and commit its
output. Every generated file carries a `GENERATED` banner comment.

**Posts are signed and dated.** `authors` and `date` are required and render as a
byline under the title, plus a `<time datetime>` matching `datePublished` in the
JSON-LD. Authorship of a post is personal in a way a multi-author paper is not,
and other people will write posts here — a reader has to be able to see whose
view this is. `authors` is a list, so a post by someone else, or by two people,
needs no schema change.

Format — YAML front matter, then a Markdown body:

- `slug` is the URL and **must match the blog's own slug**, so the redirect left
  behind on kencaldeira.com is a clean one-to-one mapping. The filename must be
  `YYYY-MM-DD-<slug>.md`; the loader enforces both, because a drift between them
  silently publishes at an unexpected path.
- `description` is the meta description; `key_point` renders above the body and
  follows the same rule as a publication's `key_finding` — one self-contained
  sentence that makes sense quoted in isolation, with no pronouns pointing back
  into the page.
- `about` is optional: the id of the publication the post is about. Set it and
  the post links to that page and the publication page links back, both
  generated, so the pair cannot drift. A dangling `about` **fails the build**
  rather than shipping a link to a 404. A post about someone else's paper, or
  about no single paper, omits it.
- Figures and videos are `:::figure` / `:::youtube` fences whose contents are
  YAML, parsed before Markdown sees them. That is what keeps `alt` required and
  the credit line generated rather than hand-typed. A figure needs `credit` and
  `license`, or `own: true` if the image is ours. Images live in
  `docs/thinking/images/<slug>/` — per-slug because the blog filenames they come
  from collide badly; five of the paper write-ups have their own `image.png`.

**Markdown is the one place autoescaping is bypassed**, in
`src/ciunit_gen/markdown_render.py`. That is deliberate and confined: an essay
that cannot link a phrase or quote an email is not an essay. **It is not licence
to loosen `model._paragraphs`** — publication prose stays plain text, because
those pages carry claims that get quoted and cited, and cross-references there go
through the structured `links`/`related` fields.

CLAUDE.md's external-link rule is enforced by code here, not by hand: post
Markdown is written as ordinary Markdown and `markdown_render` adds
`target="_blank" rel="noopener noreferrer"` to every off-domain `href` on the way
out. Don't type them into a post.

Other things worth knowing:

- **The index is the publications cover grid, newest first**, and deliberately
  shares its `.pub-*` classes rather than cloning them: the two sections are
  meant to read as one system, and a second set of rules would be a second thing
  to keep in step. A post about one of our publications borrows that
  publication's cover — the same first-page image its publication page shows —
  but the title under the box is **the post's**, because the post is what the
  box links to. The line beneath is a byline and date where a publication
  carries its citation.
- **Posts with no `about:` have no cover to borrow**, and what those boxes
  should show instead is **still to be decided**. The template falls back to a
  title plate so the build keeps working; it is a placeholder, marked as one in
  `post-index.html.j2`, not a design. All 13 posts in the first pass have a
  publication.
- **Prose styling:** the body reuses `.bio` for its column and heading scale and
  adds `.post-body` for what Markdown emits and the rest of the site never needed
  — links inside body copy, block quotes, tables. Block quotes carry a rule and
  an indent, not a colour: the handoff records that the blog marked quoted email
  with a colour class and that the distinction is meaningful, not decorative.
- **In-body links to our own papers point at their publication page**, not at the
  publisher — the same rule as bio-page citations. Links to other people's papers
  stay as DOIs.
- **Scientific claims are the user's to approve**, exactly as for publication
  pages. `description` and `key_point` are the two fields that need real
  judgment when migrating a post; where the post's own text does not yield a
  clean self-contained `key_point`, set `needs_review: true` and flag it rather
  than inventing one.
- **When a post moves, leave a redirect.** Deleting it from `_posts/` in
  `~/kcaldeira.github.io` without one breaks inbound links that have been
  indexed since as early as 2015. That work happens in that repo, not this one —
  see "When a post moves" in its `CIUNIT-HANDOFF.md`.

## Secrets

- Never commit tokens/credentials. `.gitignore` blocks `*token*`, `*.secret`,
  `.env`. If a token is ever exposed (e.g. pasted/screenshotted), treat it as
  compromised and have the user revoke it immediately.
