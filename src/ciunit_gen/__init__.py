"""Content generator for CIunit.org's papers section.

Reads content/papers/*.yaml and content/themes.yaml; writes docs/papers/,
docs/topics/, docs/papers.html and docs/sitemap.xml. Output is committed to git —
GitHub Pages runs no build step.
"""
__all__ = ["model", "render"]
