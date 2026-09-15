# CONTINUE HERE — "What We Are Thinking" (posts section)

Written 2026-09-15. **Delete this file once Ken has reviewed the 13 posts and the
redirects are left on kencaldeira.com.**

## State right now

The section is **built and all 13 paper write-ups are migrated**. Nothing is
committed. Ken has not yet read the migrated posts.

Preview: `python -m http.server -d docs 8000` → `/what-we-are-thinking.html`.
Build: `PYTHONPATH=src python -m ciunit_gen --check` →
`116 publication(s), 9 theme(s), 13 post(s) — content valid.` with no
post-related warnings. `requirements.txt` gained `Markdown>=3.5`.

## What needs Ken's eye

1. **`description` and `key_point` in all 13 front matters.** These are the two
   fields that are not in the original posts — they were written during
   migration and are scientific claims, grounded in each post's own text or its
   paper, but not author-approved.
2. **Three posts where content could not be carried across verbatim** — see
   "Losses and substitutions" below.
3. **Nothing has been checked in a browser.** No Playwright on this machine, so
   the CSS is unverified by eye at any width.

## Losses and substitutions (the honest list)

- `ocean-heat-flux-and-open-ocean-wind-energy`: the original embedded an
  *annotated* version of PNAS Fig. S10, hosted on the now-dead
  carnegieenergyinnovation.org. That annotated image is gone. The **unannotated**
  Fig. S10 was extracted from the reprint and used instead; the prose is
  otherwise Ken's. If he still has the annotated PNG, swap it in.
- `replenishing-the-wind`: three externally-hosted images were unrecoverable — a
  Twitter card at the top, a GMD illustration served from a private Gmail
  attachment URL, and the PNAS F16 (recovered as Fig. S10 from the reprint, so
  that one is fine). The sentence about the GMD illustration keeps its link to
  the paper.
- `multi-decadal-country-level-regressions-…`: the climate-damage-functions
  figure from climateinteractive.org was dropped because its reuse licence could
  not be established. The prose keeps the link.
- `the-value-of-reducing-the-green-premium` and
  `where-are-the-abundant-and-reliable-winds`: the opening screenshot of the
  journal article header was dropped from each — the publication page already
  carries the title, authors, and DOI.
- Several posts linked a publisher URL for one of our own papers; those now point
  at the publication page, per CLAUDE.md. Links to other people's papers were
  left as DOIs. Two expired signed URLs (the ERL and Springer supplements) were
  dropped rather than shipped dead.
- Ken's old `kcaldeira@carnegiescience.edu` address was replaced with
  `ken@CIunit.org` in the two posts that offered a copy of a paywalled paper.
- WordPress `swatch-white` spacer images were dropped throughout.

## Figures re-extracted at higher resolution

Where the blog copy was too small for the 820 px column and the reprint was in
`pdfs/`, the figure was re-extracted:

| post | was | now |
| --- | --- | --- |
| learning-curves… (2 figures) | 386 px wide | 2135 and 2107 px |
| hydrogen-from-curtailment (3 figures) | 715-734 px | 1458-1783 px |
| green-premium (Fig. S5) | 512 px | 2214 px |
| abundant-and-reliable-winds (Supp. Fig. 12) | 720 px | 1430 px (native embedded PNG) |
| ocean-heat-flux / replenishing (Fig. S10) | lost / external | 1614 px |

The extraction snippets are not saved as a script. If this needs doing again,
`scripts/extract_figures.py --extract <id> --figure N` handles main-paper figures
(it writes to `docs/publications/figures/<id>.png`, so move the file); supplement
figures needed ad-hoc pymupdf crops because the caption sits above the figure
there and the running head otherwise lands in the crop.

## Decisions already made (don't relitigate)

- Title **"What We Are Thinking"**, fifth nav item. Index
  `/what-we-are-thinking.html`, posts `/thinking/<slug>.html`.
- Bodies are **Markdown + YAML front matter** in `content/posts/`.
- The index is the **publications cover grid** (Ken: "modeled on the What We
  Publish page"), sharing its `.pub-*` classes. A post borrows the cover of the
  publication it is about; the title under the box is the **post's**, and the
  line below is a byline and date.
- Posts are **signed and dated** — Ken asked for this explicitly, because other
  people will write posts later.
- **Open question, deferred by Ken:** what the box shows for a post with no
  `about:`. "For the ones that we will do later that are not about a paper, we
  can do something else." Three of the 13 hit this today
  (GDP-regressions, hydrogen-from-curtailment, algae-and-anemone) and currently
  draw a placeholder title plate, marked as such in `post-index.html.j2`.

Design rationale is in `CLAUDE.md`, section "What We Are Thinking". Read it
before changing anything here.

## Publications that could now have a page

Two of the three `about:`-less posts are about papers with Ken as a co-author
that have no publication page yet. Adding them would let those posts borrow a
cover and gain a back-link:

- *Opportunities for flexible electricity loads such as hydrogen production from
  curtailed generation*, Ruggles, Dowling, Lewis and Caldeira, Adv. Appl. Energy
  3, 100051 (2021), `10.1016/j.adapen.2021.100051`, CC BY 4.0. Reprint is in
  `pdfs/`, figures already extracted under
  `docs/thinking/images/how-much-hydrogen-…/`.
- *Photo-movement in the sea anemone Aiptasia influenced by light quality and
  symbiotic association*, Foo, Liddell, Grossman et al., Coral Reefs (2019),
  `10.1007/s00338-019-01866-w`, open access.

The third (`multi-decadal-…`) is an unpublished analysis and correctly has no
publication.

## Still to do, other repo

Redirects. For each of the 13 slugs, in `~/kcaldeira.github.io`: delete the
`_posts/` file, leave a `jekyll-redirect-from` stub pointing at
`https://ciunit.org/thinking/<slug>.html`, then run `tools/images.py prune` and
`tools/verify.py`. These URLs have been indexed since 2015. **Not touched as part
of this work.**

## Also outstanding

- `PAGES-STATUS.md` (`--report`) still covers publications only; posts are not in
  it. Worth deciding if the section grows.
- The handoff's other categories — 17 "substantive science" and 22 "how research
  works" posts — remain unmigrated by design. See
  `~/kcaldeira.github.io/CIUNIT-HANDOFF.md`.
