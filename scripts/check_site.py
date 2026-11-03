#!/usr/bin/env python3
"""Validate docs/ before it ships.

Written after an automated SEO bot merged three plausible-looking but false
edits: an invented article:modified_time, a SearchAction declaring a /search
endpoint the site does not have, and preconnects to analytics that is not
installed. Each check below corresponds to one of those failures, so the same
class of mistake fails CI instead of reaching production.
"""

from __future__ import annotations

import json
import re
import sys
from datetime import date
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse, unquote

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_assets import expected as expected_min_css, inline_block_for_check

DOCS = Path(__file__).resolve().parent.parent / "docs"
SITE_EPOCH = date(2026, 1, 1)          # nothing on this site predates 2026
ALLOWED_HOSTS = {
    "integrallis.com", "schema.org", "www.sitemaps.org",
    "github.com", "medium.com", "arxiv.org", "modeljars.org",
    "rankcli.dev", "animerm.ai", "podmrk.ai", "tbltalk.ai", "moobi.dev",
    "integrallis.github.io",
}

problems: list[str] = []


def fail(page: Path, msg: str) -> None:
    problems.append(f"{page.relative_to(DOCS.parent)}: {msg}")


class Balance(HTMLParser):
    VOID = {"meta", "link", "img", "br", "hr", "input", "source", "area", "col"}

    def __init__(self) -> None:
        super().__init__()
        self.stack: list[str] = []
        self.errors: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag not in self.VOID:
            self.stack.append(tag)

    def handle_endtag(self, tag):
        if not self.stack:
            self.errors.append(f"stray </{tag}>")
        elif self.stack[-1] != tag:
            self.errors.append(f"expected </{self.stack[-1]}>, got </{tag}>")
        else:
            self.stack.pop()


def check_markup(page: Path, html: str) -> None:
    b = Balance()
    b.feed(html)
    for e in b.errors[:3]:
        fail(page, f"unbalanced markup — {e}")
    if b.stack:
        fail(page, f"unclosed tags: {', '.join(b.stack[:3])}")


def check_json_ld(page: Path, html: str) -> None:
    for raw in re.findall(r'<script type="application/ld\+json"[^>]*>(.*?)</script>', html, re.S):
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            fail(page, f"JSON-LD does not parse — {exc}")
            continue
        for key in re.findall(r'"([^"]*)"\s*:', raw):
            if "'" in key:
                fail(page, f"JSON-LD key contains quotes: \"{key}\"")
        # a declared search endpoint must actually exist
        for action in re.findall(r'"urlTemplate"\s*:\s*"([^"]+)"', json.dumps(data)):
            path = urlparse(action.split("{")[0]).path.strip("/")
            if path and not (DOCS / path).exists() and not (DOCS / f"{path}.html").exists():
                fail(page, f"schema declares an endpoint the site does not have: /{path}")



def indexed_pages() -> set[str]:
    """Paths the sitemap advertises, i.e. the pages search engines are told to index."""
    sitemap = DOCS / "sitemap.xml"
    if not sitemap.exists():
        return set()
    locs = re.findall(r"<loc>\s*([^<]+?)\s*</loc>", sitemap.read_text(encoding="utf-8"))
    return {urlparse(loc).path.lstrip("/") or "index.html" for loc in locs}


def check_schema_present(page: Path, html: str, indexed: set[str]) -> None:
    """An indexed page with no structured data is an SEO hole we have already paid for.

    A live audit found four pages shipping without JSON-LD while check_site.py
    passed, because this file only validated blocks that happened to exist.
    Redirect stubs and 404.html are not indexed and are exempt.
    """
    rel = page.relative_to(DOCS).as_posix()
    if rel not in indexed:
        return
    if not re.search(r'<script type="application/ld\+json"[^>]*>\s*\S', html):
        fail(page, "indexed page has no JSON-LD structured data")


def check_dates(page: Path, html: str) -> None:
    for prop, value in re.findall(
        r'<meta[^>]+(?:property|name)="([^"]*(?:modified|published|date)[^"]*)"[^>]+content="([^"]+)"',
        html, re.I,
    ):
        m = re.match(r"(\d{4})-(\d{2})-(\d{2})", value)
        if not m:
            continue
        when = date(*(int(g) for g in m.groups()))
        if when < SITE_EPOCH:
            fail(page, f'{prop}="{value}" predates the site — invented or stale')
        if when > date.today():
            fail(page, f'{prop}="{value}" is in the future')


def check_hosts(page: Path, html: str) -> None:
    for url in re.findall(r'(?:href|src)="(https?://[^"]+)"', html):
        host = urlparse(url).netloc.lower().removeprefix("www.")
        if host not in ALLOWED_HOSTS:
            fail(page, f"third-party host not in the allowlist: {host}")


SCHEME = re.compile(r"^[a-z][a-z0-9+.\-]*:", re.I)


def check_local_refs(page: Path, html: str) -> None:
    for ref in re.findall(r'(?:href|src)="([^"]*)"', html):
        if not ref or SCHEME.match(ref) or ref.startswith(("//", "#")):
            continue                      # absolute, protocol-relative, or same-page
        path = unquote(ref.split("#")[0].split("?")[0])
        if not path:
            continue
        base = DOCS if path.startswith("/") else page.parent
        target = base / path.lstrip("/")
        if path.endswith("/") or target.is_dir():
            target = target / "index.html"
        if not target.exists():
            fail(page, f"broken local reference: {ref}")



def check_minified_css() -> None:
    """The committed styles.min.css must match what the source minifies to.

    A stale minified file is worse than no minification: the site silently
    serves yesterday's CSS while styles.css looks correct in review. Because
    build_assets.minify is pure Python, this recomputes it offline rather than
    trusting that someone remembered to run the build.
    """
    target = DOCS / "assets" / "css" / "styles.min.css"
    if not target.exists():
        problems.append("docs/assets/css/styles.min.css is missing - run scripts/build_assets.py")
        return
    if target.read_text(encoding="utf-8") != expected_min_css():
        problems.append(
            "docs/assets/css/styles.min.css is stale - run scripts/build_assets.py"
        )

    # the CSS is inlined into every page; stale inline copies are the same bug
    block = inline_block_for_check()
    for page in sorted(DOCS.glob("*.html")):
        html = page.read_text(encoding="utf-8")
        if "<style data-inlined-css>" not in html:
            problems.append(f"{page.relative_to(DOCS.parent)}: no inlined CSS - run scripts/build_assets.py")
        elif block not in html:
            problems.append(f"{page.relative_to(DOCS.parent)}: inlined CSS is stale - run scripts/build_assets.py")
        if 'rel="stylesheet"' in html:
            problems.append(f"{page.relative_to(DOCS.parent)}: still has a render-blocking stylesheet link")


def main() -> int:
    pages = sorted(DOCS.rglob("*.html"))
    if not pages:
        print("no pages found", file=sys.stderr)
        return 1
    indexed = indexed_pages()
    for page in pages:
        html = page.read_text(encoding="utf-8")
        check_markup(page, html)
        check_json_ld(page, html)
        check_schema_present(page, html, indexed)
        check_dates(page, html)
        check_hosts(page, html)
        check_local_refs(page, html)

    check_minified_css()

    for required in ("robots.txt", "sitemap.xml", "404.html", "CNAME"):
        if not (DOCS / required).exists():
            problems.append(f"docs/{required} is missing")

    print(f"checked {len(pages)} pages")
    if problems:
        print(f"\n{len(problems)} problem(s):\n")
        for p in problems:
            print(f"  ✗ {p}")
        return 1
    print("all checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
