"""Content generator for CIunit.org's publications section.

Reads content/publications/*.yaml and content/themes.yaml; writes docs/publications/,
docs/topics/, docs/publications.html and docs/sitemap.xml. Output is committed to git —
GitHub Pages runs no build step.
"""
__all__ = ["model", "render"]
