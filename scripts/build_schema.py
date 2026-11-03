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
    "name": "Integrallis",
    "legalName": "Integrallis Software, LLC",
    "description": "Integrallis is an independent AI research and development company in Scottsdale, Arizona, building infrastructure that runs retrieval, inference and memory inside your own process, on hardware you control.",
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



# Real reader questions with direct answers, not existing prose relabelled.
# Both the visible markup and the FAQPage schema are generated from this one
# definition so they cannot drift apart. Answers are drawn only from what the
# pages already state - the product answer tracks the status labels verbatim.
FAQ = {
    "java-ai": [
        ("Do you need Python to run AI inside a Java application?",
         "No. Vectors handles retrieval and Models handles inference, both inside your JVM process. "
         "There is no Python sidecar and no separate vector service to operate."),
        ("How do model weights get into a build?",
         "ModelJARs publishes them as Maven artifacts. You add a coordinate and the weights resolve "
         "through the same dependency mechanism that brings in any other JAR."),
        ("When is a local model the wrong choice?",
         "When the measurements say so. Model qualification exists to answer that per task rather than "
         "per reputation, and we publish the cases where a frontier model wins."),
    ],
    "products": [
        ("What can I use right now?",
         "RankCLI and AniMERM.ai are live. Moobi is launching shortly at moobi.dev. PodMrk.ai is live "
         "but still a stub. OS/A and tbltalk.ai are exploratory and not yet available."),
        ("How do the products relate to the research?",
         "Each one started as a research result that needed somewhere to run. The research program and "
         "the open-source libraries are the same work at an earlier stage."),
    ],
    "research": [
        ("What does a study have to clear to be listed here?",
         "Its own stated method, limits and noise floor. Every number traces to a committed raw "
         "artifact; if a script cannot derive it, it does not appear in the paper."),
        ("Do you publish negative results?",
         "Yes. A failed hypothesis is the result. The papers keep the measurements that did not "
         "support the idea rather than dropping them."),
    ],
}

FAQ_MARKER = '<section class="faq" data-faq>'


def faq_markup(slug: str) -> str:
    rows = "\n".join(
        f"                <div class=\"faq-item\">\n"
        f"                    <h3>{q}</h3>\n"
        f"                    <p>{a}</p>\n"
        f"                </div>"
        for q, a in FAQ[slug]
    )
    return (
        f'        {FAQ_MARKER}<div class="site-shell">\n'
        f'            <div class="section-grid">\n'
        f'                <p class="section-label"><span>FAQ</span>Questions</p>\n'
        f'                <div><h2 class="content-heading">Asked and answered.</h2></div>\n'
        f'            </div>\n'
        f'            <div class="faq-list">\n{rows}\n            </div>\n'
        f'        </div></section>\n'
    )


def faq_schema(slug: str) -> dict:
    return {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": q,
                "acceptedAnswer": {"@type": "Answer", "text": a},
            }
            for q, a in FAQ[slug]
        ],
    }

def newest_article_date() -> str | None:
    """dateModified for the Blog page, taken from the feed rather than invented."""
    data = DOCS / "assets" / "data" / "articles.json"
    if not data.exists():
        return None
    articles = json.loads(data.read_text(encoding="utf-8"))
    return max(a["published"] for a in articles) if articles else None


def page_graph(slug: str, ptype: str, crumb: str | None, title: str, desc: str) -> list[dict]:
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

    # Separate top-level blocks, NOT one @graph. Measured: with the entities
    # inside an @graph the auditor reported NO_ORGANIZATION_SCHEMA on all six
    # pages, including index.html which had previously passed with a top-level
    # Organization, and NO_MAIN_ENTITY_OF_PAGE appeared on all six. It does not
    # traverse @graph, so each entity gets its own script tag.
    org = dict(ORGANIZATION)
    org["@context"] = "https://schema.org"
    org["mainEntityOfPage"] = {"@type": "WebPage", "@id": page["@id"]}
    site = dict(WEBSITE)
    site["@context"] = "https://schema.org"
    page["@context"] = "https://schema.org"
    page["mainEntity"] = {"@id": ORG_ID}
    out = [org, site, page]
    if slug in FAQ:
        out.append(faq_schema(slug))
    return out


def main() -> int:
    for slug, (ptype, crumb) in PAGES.items():
        path = DOCS / f"{slug}.html"
        html = path.read_text(encoding="utf-8")
        title = re.search(r"<title>(.*?)</title>", html, re.S).group(1)
        desc = re.search(r'<meta name="description" content="(.*?)"', html, re.S).group(1)
        blocks = []
        for entity in page_graph(slug, ptype, crumb, title, desc):
            payload = json.dumps(entity, indent=2, ensure_ascii=False)
            body = "\n" + "\n".join("    " + l for l in payload.split("\n")) + "\n    "
            blocks.append(MARKER + body + "</script>")
        new_block = "\n    ".join(blocks)

        if MARKER in html:
            # strip every previously generated block, then insert the new set
            html = re.sub(
                r'[ \t]*' + re.escape(MARKER) + r'.*?</script>\n?',
                "",
                html,
                flags=re.S,
            )
            html = html.replace("</head>", f"    {new_block}\n</head>", 1)
        else:
            # drop whatever hand-written blocks were there, except the feed-owned one
            html = re.sub(
                r'[ \t]*<script type="application/ld\+json">.*?</script>\n',
                "",
                html,
                flags=re.S,
            )
            html = html.replace("</head>", f"    {new_block}\n</head>", 1)
        if slug in FAQ:
            block = faq_markup(slug)
            start = html.find(FAQ_MARKER)
            if start != -1:
                line = html.rfind("\n", 0, start) + 1
                close = html.index("</section>", start) + len("</section>\n")
                html = html[:line] + html[close:]
            strip = html.index('<section class="contact-strip">')
            line = html.rfind("\n", 0, strip) + 1
            html = html[:line] + block + html[line:]

        path.write_text(html, encoding="utf-8")
        extra = " + FAQPage" if slug in FAQ else ""
        print(f"{slug}.html  <- blocks[Organization, WebSite, {ptype}]{extra}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
