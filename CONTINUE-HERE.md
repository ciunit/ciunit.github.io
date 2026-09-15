# CONTINUE HERE — "What We Are Thinking" (posts section)

Written 2026-09-15. Delete this file once the 13-post migration is done.

## State right now

The section is **built and working, with one post migrated as a proof**. Nothing
is committed: `git status` shows ~155 changed/new files on top of `cf728de`.
That is expected, not damage — see "What the diff contains" below.

Preview: `python -m http.server -d docs 8000` →
`/what-we-are-thinking.html` and `/thinking/where-do-the-winds-come-from.html`.

Build: `PYTHONPATH=src python -m ciunit_gen --check` should say
`116 publication(s), 9 theme(s), 1 post(s) — content valid.` with no
post-related warnings. `requirements.txt` gained `Markdown>=3.5`; it is already
installed in `.venv`.

**Ken has not yet looked at the rendered result.** The stopping point was
deliberate: see the shape before sinking twelve more conversions into it. Ask
before proceeding to stage 2 if he has not said.

## Decisions already made (don't relitigate)

- Section title **"What We Are Thinking"**, fifth nav item after "What We
  Publish". Index `/what-we-are-thinking.html`, posts `/thinking/<slug>.html`.
- Bodies are **Markdown + YAML front matter** in `content/posts/`, not the
  plain-text YAML the publications use.
- First pass is **the 13 paper write-ups only**. The handoff's other two
  CIunit-appropriate categories (17 "substantive science", 22 "how research
  works") are a later decision; `about:` is already optional so they need no
  new machinery.
- Posts are **signed and dated** — Ken asked for this explicitly, because other
  people will write posts later.
- The index is a **reverse-chronological list, not a cover grid**.

The full design rationale is in `CLAUDE.md`, section "What We Are Thinking".
Read that before changing anything here.

## What the diff contains

New:
- `src/ciunit_gen/posts.py` — `Post`/`PostFigure`/`YouTube`/`Prose`, front-matter
  and fence parsing, validation.
- `src/ciunit_gen/markdown_render.py` — the Markdown wrapper. The **only** place
  autoescaping is bypassed, and the place the external-link target/rel rule is
  enforced in code.
- `src/ciunit_gen/templates/post.html.j2`, `post-index.html.j2`.
- `content/posts/2017-03-05-where-do-the-winds-come-from.md` and
  `docs/thinking/` (generated page + `images/<slug>/`).

Modified:
- `_base.html.j2` + all **13 hand-written `docs/*.html`** — the new nav link.
  This is why 148 generated pages show a diff; for every publication page except
  `ahbe-2017-available-potential-energy` it is that **one line and nothing else**.
- `render.py` (`post_jsonld`, `render_post`, `render_post_index`, posts in the
  sitemap, `render_paper` gained a `posts` argument), `__main__.py` (load,
  validate, warn, render), `paper.html.j2` (the reciprocal back-link),
  `docs/css/style.css` (one appended `.post-*` / `.think-*` block; nothing
  existing was touched), `CLAUDE.md`, `README.md`, `requirements.txt`.

## Next steps

**Stage 2** — migrate `where-are-the-abundant-and-reliable-winds` (2,436 words,
10 images), the long post, to exercise figures and tables.

**Stage 3** — the remaining 11.

Per post, the mechanical part:

1. Copy the body from `~/kcaldeira.github.io/_posts/<file>.md`.
2. `{% include figure.html src=… caption=… link=… %}` → a `:::figure` fence
   (YAML inside: `file`, `alt`, `caption`, `credit`, `license`, optional `link`;
   or `own: true` for our own images). **`alt` is required and must describe what
   the figure shows** — the original posts mostly have none, so it has to be
   written.
3. `{% include youtube.html id=… %}` → `:::youtube`.
4. Copy images from `~/kcaldeira.github.io/assets/images/YYYY/MM/` into
   `docs/thinking/images/<slug>/`. Drop the `swatch-white_*.png` spacers — they
   are WordPress layout artefacts, not content.
5. Rewrite in-body links to **our own** papers to point at
   `../publications/<id>.html`; leave other people's papers as DOIs.
6. `slug` must be the blog's own slug, and the filename `YYYY-MM-DD-<slug>.md`.

The part that is **not** mechanical, and needs Ken's approval: `description` and
`key_point`. Ground both in the post's own text or the paper. Where the post does
not yield a clean self-contained `key_point`, set `needs_review: true` and flag
it rather than inventing one.

## Post → publication mapping (verified by DOI grep — use as-is)

| Blog slug | `about:` |
| --- | --- |
| where-are-the-abundant-and-reliable-winds | `antonini-2024-wind-droughts` |
| the-value-of-reducing-the-green-premium | `caldeira-2023-green-premium` |
| replenishing-the-wind | `antonini-2021-spatial-constraints` |
| climate-change-as-an-incentive-to-future-human-migration-2 | `chen-2020-migration-incentive` |
| geophysical-constraints-on-the-reliability-of-solar-and-wind-power-in-the-united-states | `shaner-2018-us-reliability` |
| ocean-heat-flux-and-open-ocean-wind-energy | `possner-2017-open-ocean-wind` |
| learning-curves-and-clean-energy-rd-incremental-advances-or-aim-for-breakthroughs | `shayegh-2017-clean-energy-rd` |
| will-using-a-carbon-tax-for-revenue-generate-create-an-incentive-to-continue-co2-emissions | `wang-2017-carbon-tax-incentive` |
| where-do-the-winds-come-from | `ahbe-2017-available-potential-energy` ✅ done |
| reversal-of-radiocarbon-flux-into-the-ocean | `caldeira-1998-radiocarbon-efflux` |

Three have **no publication page** and ship with `about:` omitted:

- `multi-decadal-country-level-regressions-on-gdp-growth-and-temperature-change`
  — about others' papers (`10.1126/sciadv.add3726`).
- `who-is-controlling-who-the-curious-case-of-the-algae-and-the-sea-anemone`
  — *Coral Reefs* `10.1007/s00338-019-01866-w`; candidate for a publication page.
- `how-much-hydrogen-could-we-produce-without-adding-additional-generation-capacity`
  — *Adv. Appl. Energy* `10.1016/j.adapen.2021.100051`; likewise.

Source list with word/image counts: `~/kcaldeira.github.io/CIUNIT-HANDOFF.md`.

## Known gaps

- **Nothing has been checked in a real browser.** The browser-automation skill
  has no Playwright install on this machine, so the CSS — including the 400 px
  mobile width — is unverified by eye. All verification so far is static
  analysis of the generated HTML. Worth a look at both widths.
- **Redirects are not done, and are out of scope for this repo.** When a post
  moves, `~/kcaldeira.github.io` needs the `_posts/` file deleted and a
  `jekyll-redirect-from` stub left at the old URL pointing to
  `https://ciunit.org/thinking/<slug>.html`, then `tools/images.py prune` and
  `tools/verify.py`. These URLs have been indexed since 2015; deleting without a
  redirect breaks live inbound links. See "When a post moves" in that repo's
  `CIUNIT-HANDOFF.md`.
- `PAGES-STATUS.md` (`--report`) still covers publications only. Posts are not
  in it. Fine for now; worth deciding if the section grows.
