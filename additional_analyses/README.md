# Additional analyses

Analyses by the Conceptual Investigations Unit that go beyond what a published paper
reports, such as a reanalysis of a paper's published data. Each one supports the
"Additional analysis" section of a publication page on ciunit.org.

This folder is outside `docs/`, so GitHub Pages does not serve it. The pages link here
on GitHub instead.

## Layout

One subfolder per analysis, named after the publication id, so it matches
`content/publications/<id>.yaml` and the page at `ciunit.org/publications/<id>.html`:

```
<publication-id>/
  README.md        what was done, from what data, and how to reproduce it
  scripts/         the analysis code
  data/input/      the input data, exactly as obtained, with its licence
  data/output/     everything the scripts write
```

## Rules

- **Use the data the paper cites,** taken from its published archive (Zenodo, journal
  supplement, and so on), not a working copy. Record where it came from and its checksum
  in the README, so anyone can confirm it is the same file.
- **Commit the outputs** the publication page quotes, so each number on the page can be
  traced to a file here.
- **Only data whose licence allows redistribution** is committed, with its licence file
  alongside. Publisher PDFs are never committed (the repo's `.gitignore` blocks `*.pdf`).
- The page's `additional_analysis` block cites this folder in its `source`. See
  `PUBLICATION-PAGES.md`.

## Index

| Analysis | Publication page |
| --- | --- |
| [`carlino-2025-technology-learning-rates`](carlino-2025-technology-learning-rates/) | [Variability of technology learning rates](https://ciunit.org/publications/carlino-2025-technology-learning-rates.html) |
