#!/usr/bin/env python3
"""Build the site's article data from Brian Sam-Bodden's public Medium RSS feed."""

from __future__ import annotations

import argparse
import html
import json
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime
from email.utils import parsedate_to_datetime
from html.parser import HTMLParser
from pathlib import Path

DEFAULT_FEED = "https://medium.com/feed/@bsbodden_68805"
DEFAULT_OUTPUT = Path("docs/assets/data/articles.json")
CONTENT_NS = "{http://purl.org/rss/1.0/modules/content/}encoded"


class TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        self.parts.append(data)


def text_content(markup: str) -> str:
    parser = TextExtractor()
    parser.feed(markup)
    text = html.unescape(" ".join(parser.parts))
    return re.sub(r"\s+", " ", text).strip()


def excerpt_from(markup: str, limit: int = 210) -> str:
    paragraphs = re.findall(r"<p(?:\s[^>]*)?>(.*?)</p>", markup, flags=re.I | re.S)
    candidates = [text_content(paragraph) for paragraph in paragraphs]
    excerpt = next((value for value in candidates if len(value) >= 90), "")
    if not excerpt:
        excerpt = text_content(markup)
    if len(excerpt) <= limit:
        return excerpt
    shortened = excerpt[: limit + 1].rsplit(" ", 1)[0]
    return f"{shortened}…"


def clean_url(url: str) -> str:
    parsed = urllib.parse.urlsplit(url)
    return urllib.parse.urlunsplit((parsed.scheme, parsed.netloc, parsed.path, "", ""))


def category_for(categories: list[str]) -> str:
    normalized = {category.lower() for category in categories}
    if normalized & {"java", "spring-ai", "spring-boot", "object-storage"}:
        return "Java AI"
    if normalized & {"agentic-code-generation", "code-quality-tools", "agentic-coding"}:
        return "Agentic coding"
    return categories[0].replace("-", " ").title() if categories else "Field notes"


def parse_feed(xml_bytes: bytes) -> list[dict[str, str]]:
    root = ET.fromstring(xml_bytes)
    articles: list[dict[str, str]] = []

    for item in root.findall("./channel/item"):
        title = (item.findtext("title") or "").strip()
        url = clean_url((item.findtext("link") or "").strip())
        raw_date = (item.findtext("pubDate") or "").strip()
        content = item.findtext(CONTENT_NS) or ""
        categories = [node.text.strip() for node in item.findall("category") if node.text]
        if not title or not url or not raw_date:
            continue

        published = parsedate_to_datetime(raw_date)
        articles.append(
            {
                "title": title,
                "url": url,
                "published": published.date().isoformat(),
                "dateLabel": f"{published.strftime('%b')} {published.day}, {published.year}",
                "category": category_for(categories),
                "excerpt": excerpt_from(content),
            }
        )

    return sorted(articles, key=lambda item: datetime.fromisoformat(item["published"]), reverse=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--feed", default=DEFAULT_FEED)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    request = urllib.request.Request(args.feed, headers={"User-Agent": "integrallis.com article sync"})
    with urllib.request.urlopen(request, timeout=30) as response:
        articles = parse_feed(response.read())

    if not articles:
        raise SystemExit("Medium feed returned no articles; preserving the existing data file")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(articles[:12], indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {len(articles[:12])} articles to {args.output}")


if __name__ == "__main__":
    main()
