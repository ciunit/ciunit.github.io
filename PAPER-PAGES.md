# How to add a paper page

The procedure for the papers section of CIunit.org. `CLAUDE.md` holds the *writing*
conventions and the reasoning behind them; this file is the *mechanics*.

Nothing under `docs/papers/`, `docs/topics/`, `docs/papers.html`, or
`docs/sitemap.xml` is edited by hand. They are generated from `content/`.

---

## Layout

```
content/papers/<id>.yaml     source of truth, one file per paper
content/themes.yaml          theme pages
content/figure-picks.json    which figure of each paper we use
content/survey-cache.json    gitignored — DOI metadata cache
content/pdf-map.json         PDF filename -> DOI (committed; the PDFs are not)

pdfs/                        gitignored — reprint library, never committed
docs/papers/figures/         the only images that ship

src/ciunit_gen/              generator
scripts/                     helpers (below)
PAPERS-STATUS.md             every cited DOI, and whether it can have a page
PAGES-STATUS.md              every published page, with figure resolution
```

## Commands

```bash
pip install -r requirements.txt

PYTHONPATH=src python -m ciunit_gen --check    # validate content, write nothing
PYTHONPATH=src python -m ciunit_gen            # build the site
PYTHONPATH=src python -m ciunit_gen --report   # refresh PAGES-STATUS.md

python3 scripts/survey_papers.py               # survey every cited DOI (slow, network)
python3 scripts/survey_papers.py --markdown > PAPERS-STATUS.md
python3 scripts/check_licenses.py <doi>        # metadata + figure reuse rights
python3 scripts/match_pdfs.py                  # map pdfs/ to DOIs (slow)

python3 scripts/extract_figures.py --list      # pages needing a figure, and whether a PDF exists
python3 scripts/extract_figures.py --contact <id>   # contact sheet of all figures
python3 scripts/extract_figures.py --extract <id> --figure N
python3 scripts/extract_figures.py --pages <id> [--page N]   # page images, for cropping by eye
python3 scripts/extract_figures.py --extract <id> --page N --rect x0,y0,x1,y1
python3 scripts/rebuild_figures.py [<id> ...]  # re-extract from figure-picks.json
```

---

## Adding one paper

**1. Check it can be written.** Look it up in `PAPERS-STATUS.md`. A page needs a
verifiable key finding, which means a reachable abstract or the PDF in hand. If
neither exists, do not write the page — an invented finding is worse than no page.

**2. Get the citation from Crossref, never by hand.**

```bash
python3 scripts/check_licenses.py 10.1038/s41467-021-26355-z
```

This gives authors, journal, volume, pages/article number, date, and the figure
reuse verdict. Note that Nature-family papers use an **article number**, which
goes in `pages:`.

**3. Write `content/papers/<id>.yaml`.** Id format is
`<lead-author>-<year>-<short-slug>`. It becomes the URL, so choose once and don't
rename — renaming breaks inbound links.

**4. Add a figure** (below), or leave it out; the generator warns but still builds.

**5. Build and check.**

```bash
PYTHONPATH=src python -m ciunit_gen --check && PYTHONPATH=src python -m ciunit_gen
PYTHONPATH=src python -m ciunit_gen --report
```

---

## The YAML schema

Required — the build fails without these:

| field | notes |
| --- | --- |
| `id` | must equal the filename stem |
| `doi` | as printed, any case |
| `title` | from Crossref |
| `authors` | list, full given names |
| `journal`, `year` | |
| `description` | the `<meta description>`; one sentence, states the finding |
| `question` | list of paragraphs — why the paper was written |
| `key_finding` | **one self-contained sentence carrying the number** |
| `findings` | list of paragraphs |
| `matters` | list of paragraphs |

Optional: `date`, `volume`, `pages`, `themes` (list of theme ids), `links`
(list of `{label, url}`), `related` (list of paper ids), `figure`, `needs_review`.

`needs_review: true` marks claims not yet verified against the paper. It renders
nothing but is listed in `PAGES-STATUS.md` and warned about at build time. Use it
whenever the summary rests on something you could not read directly, and say why
in a YAML comment.

### YAML gotcha that will bite you

Prose is **plain text and autoescaped** — content files can never inject markup.
But a plain scalar cannot contain `": "`. This parses:

```yaml
  - >
    The regions combine three properties: high power density, low variability.
```

and this is a syntax error:

```yaml
  - The regions combine three properties: high power density, low variability.
```

If a paragraph contains a colon followed by a space, it must be a `- >` block
scalar. Same for em dashes at end of line. Run `--check` after every edit.

### Themes

`content/themes.yaml`. Required: `id`, `title`, `question`, `short_answer`,
`description`. Optional: `why_it_matters`, `evidence` (list of `{claim, paper}`),
`methods`. A paper with no theme lands under "Other papers" on the index.

Index sections are ordered by their most recent paper; papers within a section are
newest first. Both are automatic.

---

## Figures

### Deciding whether you may republish it

Run `check_licenses.py`. Three outcomes:

| Verdict | What to do |
| --- | --- |
| CC BY / CC BY-SA | Reproduce with attribution. Resizing fine. |
| CC BY-NC-ND / BY-ND | Reproduce **unmodified** — no resizing, keep the native-resolution PNG. `rebuild_figures.py` detects ND from the licence data and skips conversion automatically. |
| Not openly licensed | Rely on Ken's author-reuse-on-own-website rights. Record `license: author reuse rights`. |

`figure.credit` and `figure.license` are **required data fields**, so the caption
credit line is generated rather than hand-typed.

### Extracting

```bash
python3 scripts/extract_figures.py --contact <id>   # look at the contact sheet
python3 scripts/extract_figures.py --extract <id> --figure 3
```

Record the choice in `content/figure-picks.json`, then convert with
`rebuild_figures.py`, which renders at 600 dpi and writes WebP at ≤1600 px.
**Always record the pick** — it is what makes the whole set reproducible when the
extractor changes.

A pick is one of three forms:

```json
"ban-weiss-2010-optimization": 3
"davis-2011-supply-chain-emissions": {"figure": 1, "trim": {"right": 0.06}}
"pagani-2009-terrestrial-plants-co2": {"page": 3, "rect": [303, 44, 563, 210]}
```

`trim` cuts a fraction off a side of the detected region; keys are
`left`/`right`/`top`/`bottom`. `page` (1-based) with `rect` (PDF points) skips
caption detection and renders exactly that rectangle — see "Cropping by eye"
below for when that is needed and how to find the numbers.

Then add the `figure:` block: `file`, `alt`, `caption`, `license`, `credit` are
required; `source_figure`, `license_url`, `source`, `modification` optional.
Alt text must describe what the figure *shows* — retrieval systems read it and
cannot see the image.

### Quality

`PAGES-STATUS.md` tiers each figure against the 820 px content column: `good`
≥1200 px, `adequate` 800–1199, `low` 500–799, `very low` <500. Vector figures
gain real detail at higher dpi, so re-extract anything below `good` at
`--dpi 600` or higher rather than upscaling.

### Failure modes the extractor already handles — don't "fix" these

Each was silently wrong rather than obviously broken, so they are easy to
reintroduce:

- **Embedded-image extraction finds nothing.** Scientific figures are vector art.
  The extractor locates the caption and renders the region above it.
- **Adjacent columns.** Inclusion uses a *centre* test, not an overlap test. An
  overlap test drags the neighbouring column's prose into the crop.
- **Runaway upward growth.** The region grows contiguously up from the caption and
  stops at the first block of body text; otherwise it swallows the previous figure.
- **Axis labels are text, not drawings.** A second pass pulls in short text
  abutting the region, or the crop shears off the axes.
- **Journal furniture.** Running heads and "please cite this article" banners are
  dropped by margin bands; rotated spine labels are dropped by an aspect-ratio test.
- **No horizontal clip.** Clipping to the caption width shears the outer panels off
  figures wider than their caption. A horizontal-growth pass was tried and reverted
  — it fixed one page-wide figure and broke several two-column ones.
- **The wrong PDF.** Several files can carry the same DOI, because a paper that
  *cites* it prints the DOI in its references. Selection scores candidates by title
  overlap with the first page; a size-based tie-break picks the wrong file.

The `--contact` output flags `BODY TEXT IN CROP` when a crop still contains prose.
That should be empty for every chosen figure.

### Cropping by eye

Two situations need an explicit rectangle rather than a detected region:

- **A scan with no text layer.** `--contact` prints "no figures detected": there is
  no caption to anchor a crop to.
- **A detected region that shears something off.** `trim` can only shrink a region,
  never grow one, so a crop that clips a rotated axis title or a figure-row label
  cannot be fixed with `trim`.

```bash
python3 scripts/extract_figures.py --pages <id>                    # every page
python3 scripts/extract_figures.py --pages <id> --page 3 --dpi 130 # one, larger
```

`--pages` prints each page's rectangle in PDF points alongside the image path.
Read the figure's bounds off the image as fractions of the page and multiply by
that rectangle — do not assume a page is A4, since several of these are not. Then:

```bash
python3 scripts/extract_figures.py --extract <id> --page 3 --rect 303,44,563,210
```

Look at the result before recording it. Getting a rectangle right normally takes
two or three passes: the usual faults are a running head or caption line caught at
the edge, and an axis title left just outside.

### Papers the pipeline cannot help with

- **No PDF, publisher blocks automated access.** Springer Nature, Copernicus, and
  Springer serve figures over the web; IOP, Wiley/AGU, Elsevier, PNAS, and Science
  refuse. An open licence does *not* imply a reachable figure — several IOP papers
  here are CC BY but unreachable.

---

## Verification before handing over

```bash
PYTHONPATH=src python -m ciunit_gen && PYTHONPATH=src python -m ciunit_gen   # twice: must be byte-identical
python -m http.server -d docs 8000
```

Check: every internal link resolves; every `href="http…"` has
`target="_blank" rel="noopener noreferrer"`; JSON-LD parses on every page; no
nested `<a>` (the index cards are the risk); `git status` shows nothing from
`pdfs/`.

---

## Where the work stands

57 paper pages, 9 themes, 48 with figures, none below `good` resolution.
`ken-caldeira.html` has 55 of its 61 cited papers covered.

Outstanding:

1. **8 figureless pages with no PDF** — `caldeira-kasting-1993-warming-potentials`,
   `duffy-1997-sea-ice-salinity`, `govindasamy-2000-first-simulations`,
   `li-2024-storage-portfolios`, `rampino-2021-tetrapod-periodicity`,
   `thomas-2025-aviation-cirrus`, `wongel-2025-cooling-deficit`,
   `wongel-2026-solar-process-heat`. Each needs a figure supplied by an author, or a
   reachable one on the publisher's site. Plus `davis-2018-net-zero-energy-systems`
   (page-wide schematic, deliberately text-only).
2. **2 pages flagged `needs_review`** — `caldeira-kasting-1993-warming-potentials`
   and `caldeira-1990-deccan-volcanism`. Both need an author to confirm the claims.
3. **6 of `ken-caldeira.html`'s 61 papers still have no page**, all
   `blocked-no-abstract` with no PDF in `pdfs/` — Caldeira 1989, Caldeira 1992,
   Caldeira & Kasting 1992, Hoffert et al. 1998, Caldeira & Wickett 2003, and
   Carlino et al. 2025. A reprint of any of them unblocks its page.
4. **Deferred:** the 61 bio-page DOI links still go straight to doi.org rather than
   to the local paper pages, and `climate-and-climate-impacts.html` cites four
   papers that now have pages without linking to them. Don't start either without
   asking.
