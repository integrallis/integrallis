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
    for raw in re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.S):
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


def main() -> int:
    pages = sorted(DOCS.rglob("*.html"))
    if not pages:
        print("no pages found", file=sys.stderr)
        return 1
    for page in pages:
        html = page.read_text(encoding="utf-8")
        check_markup(page, html)
        check_json_ld(page, html)
        check_dates(page, html)
        check_hosts(page, html)
        check_local_refs(page, html)

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
