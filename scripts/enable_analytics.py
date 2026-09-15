#!/usr/bin/env python3
"""Inject (or remove) GA4 and Google Search Console verification across docs/*.html.

Nothing is added to the site until this is run with real values, so the pages never
ship a placeholder that fires a broken third-party request.

    python3 scripts/enable_analytics.py --ga4 G-XXXXXXXXXX
    python3 scripts/enable_analytics.py --gsc <verification-token>
    python3 scripts/enable_analytics.py --ga4 G-XXXXXXXXXX --gsc <token>
    python3 scripts/enable_analytics.py --remove

Re-running replaces what is already there, so it is safe to run repeatedly.
"""
import argparse, glob, os, re, sys

DOCS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs")
GA_START, GA_END = "<!-- ga4:start -->", "<!-- ga4:end -->"
GSC_START, GSC_END = "<!-- gsc:start -->", "<!-- gsc:end -->"


def strip(html, start, end):
    return re.sub(re.escape(start) + r".*?" + re.escape(end) + r"\s*", "", html, flags=re.S)


def ga4_block(mid):
    return (
        f'{GA_START}\n'
        f'    <script async src="https://www.googletagmanager.com/gtag/js?id={mid}"></script>\n'
        f'    <script>\n'
        f'      window.dataLayer = window.dataLayer || [];\n'
        f'      function gtag(){{dataLayer.push(arguments);}}\n'
        f'      gtag("js", new Date());\n'
        f'      gtag("config", "{mid}");\n'
        f'    </script>\n'
        f'    {GA_END}\n    '
    )


def gsc_block(token):
    return f'{GSC_START}\n    <meta name="google-site-verification" content="{token}">\n    {GSC_END}\n    '


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ga4", help="GA4 measurement ID, e.g. G-XXXXXXXXXX")
    ap.add_argument("--gsc", help="Search Console verification token")
    ap.add_argument("--remove", action="store_true", help="strip both from every page")
    a = ap.parse_args()

    if not (a.ga4 or a.gsc or a.remove):
        ap.error("give --ga4, --gsc, or --remove")
    if a.ga4 and not re.fullmatch(r"G-[A-Z0-9]{6,}", a.ga4):
        ap.error(f"'{a.ga4}' does not look like a GA4 measurement ID (expected G-XXXXXXXXXX)")

    pages = sorted(glob.glob(os.path.join(DOCS, "*.html")))
    if not pages:
        sys.exit(f"no pages found under {DOCS}")

    for path in pages:
        html = open(path).read()
        before = html
        html = strip(strip(html, GA_START, GA_END), GSC_START, GSC_END)
        if not a.remove:
            insert = ""
            if a.gsc:
                insert += gsc_block(a.gsc)
            if a.ga4:
                insert += ga4_block(a.ga4)
            if insert:
                html = html.replace("<title>", insert + "<title>", 1)
        if html != before:
            open(path, "w").write(html)
        print(f"{'stripped' if a.remove else 'updated'}  {os.path.basename(path)}")


if __name__ == "__main__":
    main()
