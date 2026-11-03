#!/usr/bin/env python3
"""Generate the page-level JSON-LD for every indexed page.

Written after a live audit regression: adding a *minimal* schema block to five
pages removed SCHEMA_MISSING but introduced NO_ENTITY_SCHEMA,
NO_ORGANIZATION_SCHEMA, NO_SCHEMA_SAMEAS and LOW_ENTITY_CONSISTENCY, because
those checks only run once a page has schema at all. Thin schema scores worse
than none. Generating every block from one definition keeps the organization
entity identical across pages, which is what the consistency check wants.

The article ItemList on writing.html is NOT written here - sync_medium.py owns
it, so it is derived from the feed and cannot go stale.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

DOCS = Path(__file__).resolve().parent.parent / "docs"
SITE = "https://integrallis.com"
ORG_ID = f"{SITE}/#organization"
SITE_ID = f"{SITE}/#website"

# One definition, emitted on every page. Matches the block index.html already
# carried, so the entity name and sameAs links are consistent site-wide.
ORGANIZATION = {
    "@type": "Organization",
    "@id": ORG_ID,
    "name": "Integrallis Software, LLC",
    "alternateName": "Integrallis",
    "url": f"{SITE}/",
    "logo": {
        "@type": "ImageObject",
        "url": f"{SITE}/assets/images/logo-full-dark.png",
    },
    "image": f"{SITE}/assets/images/og-integrallis.jpg",
    "email": "info@integrallis.com",
    "telephone": "+1-480-463-4962",
    "foundingDate": "2002",
    "address": {
        "@type": "PostalAddress",
        "addressLocality": "Scottsdale",
        "addressRegion": "AZ",
        "addressCountry": "US",
    },
    "sameAs": [
        "https://github.com/integrallis",
        "https://medium.com/@bsbodden_68805",
    ],
}

WEBSITE = {
    "@type": "WebSite",
    "@id": SITE_ID,
    "name": "Integrallis",
    "url": f"{SITE}/",
    "publisher": {"@id": ORG_ID},
}

# slug -> (page @type, breadcrumb label)
PAGES = {
    "index": ("WebPage", None),
    "research": ("CollectionPage", "Research"),
    "java-ai": ("WebPage", "Java AI"),
    "products": ("CollectionPage", "Products"),
    "writing": ("Blog", "Writing"),
    "open-source": ("CollectionPage", "Open source"),
}

MARKER = '<script type="application/ld+json" data-page-schema>'


def newest_article_date() -> str | None:
    """dateModified for the Blog page, taken from the feed rather than invented."""
    data = DOCS / "assets" / "data" / "articles.json"
    if not data.exists():
        return None
    articles = json.loads(data.read_text(encoding="utf-8"))
    return max(a["published"] for a in articles) if articles else None


def page_graph(slug: str, ptype: str, crumb: str | None, title: str, desc: str) -> dict:
    url = f"{SITE}/" if slug == "index" else f"{SITE}/{slug}.html"
    page = {
        "@type": ptype,
        "@id": f"{url}#webpage",
        "url": url,
        "name": title,
        "description": desc,
        "isPartOf": {"@id": SITE_ID},
        "publisher": {"@id": ORG_ID},
        "about": {"@id": ORG_ID},
        "inLanguage": "en-US",
    }
    if crumb:
        page["breadcrumb"] = {
            "@type": "BreadcrumbList",
            "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Home", "item": f"{SITE}/"},
                {"@type": "ListItem", "position": 2, "name": crumb, "item": url},
            ],
        }
    if slug == "writing":
        when = newest_article_date()
        if when:
            page["dateModified"] = when
    return {"@context": "https://schema.org", "@graph": [ORGANIZATION, WEBSITE, page]}


def main() -> int:
    for slug, (ptype, crumb) in PAGES.items():
        path = DOCS / f"{slug}.html"
        html = path.read_text(encoding="utf-8")
        title = re.search(r"<title>(.*?)</title>", html, re.S).group(1)
        desc = re.search(r'<meta name="description" content="(.*?)"', html, re.S).group(1)
        payload = json.dumps(page_graph(slug, ptype, crumb, title, desc), indent=2, ensure_ascii=False)
        body = "\n" + "\n".join("    " + l for l in payload.split("\n")) + "\n    "
        new_block = MARKER + body + "</script>"

        if MARKER in html:
            start = html.index(MARKER)
            end = html.index("</script>", start) + len("</script>")
            html = html[:start] + new_block + html[end:]
        else:
            # drop whatever hand-written blocks were there, except the feed-owned one
            html = re.sub(
                r'[ \t]*<script type="application/ld\+json">.*?</script>\n',
                "",
                html,
                flags=re.S,
            )
            html = html.replace("</head>", f"    {new_block}\n</head>", 1)
        path.write_text(html, encoding="utf-8")
        print(f"{slug}.html  <- @graph[Organization, WebSite, {ptype}]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
