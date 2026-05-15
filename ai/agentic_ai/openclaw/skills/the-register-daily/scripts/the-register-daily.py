#!/usr/bin/env python3
"""Fetch The Register RSS feeds and generate a daily digest report.

Uses only Python stdlib (no pip deps).
"""

import re
import sys
from datetime import datetime, timedelta, timezone
from html import unescape
from pathlib import Path
from urllib.request import Request, urlopen
from xml.etree import ElementTree

RSS_NS = "{http://purl.org/rss/1.0/}"
ATOM_NS = "{http://www.w3.org/2005/Atom}"

FEEDS = [
    {
        "name": "AI & ML",
        "url": "https://api.theregister.com/api/v1/article?query=tag:%22ai%20and%20ml%22&orderBy=published&site_id=2&remapper=rss",
    },
    {
        "name": "Offbeat",
        "url": "https://api.theregister.com/api/v1/article?query=tag:offbeat&orderBy=published&site_id=2&remapper=rss",
    },
]


def strip_html(text: str) -> str:
    """Remove HTML tags from text."""
    return re.sub(r"<[^>]+>", "", text).strip()


def fetch_feed(url: str) -> list[dict]:
    """Fetch an RSS/Atom feed and return a list of item dicts."""
    req = Request(url, headers={"User-Agent": "the-register-daily/1.0"})
    with urlopen(req, timeout=30) as resp:
        raw = resp.read().decode(resp.headers.get_content_charset() or "utf-8")

    root = ElementTree.fromstring(raw)
    items = []

    if root.tag == f"{ATOM_NS}feed":
        # Atom
        for entry in root.findall(f"{ATOM_NS}entry"):
            link_el = entry.find(f"{ATOM_NS}link")
            items.append({
                "title": (entry.findtext(f"{ATOM_NS}title") or "").strip(),
                "link": (link_el.get("href") if link_el is not None else "").strip(),
                "description": (
                    (entry.findtext(f"{ATOM_NS}summary") or entry.findtext(f"{ATOM_NS}content") or "").strip()
                ),
                "published": (entry.findtext(f"{ATOM_NS}published") or entry.findtext(f"{ATOM_NS}updated") or "").strip(),
            })
    elif root.tag == 'channel':
        # RSS 1.0 (RDF)
        for item in root.findall('item'):
            items.append({
                'title': (item.findtext('title') or '').strip(),
                'link': (item.findtext('link') or '').strip(),
                'description': (item.findtext('description') or '').strip(),
                'published': (item.findtext('pubDate') or '').strip(),
            })
    elif root.tag == 'rss':
        # RSS 2.0 — items are under <channel>
        channel = root.find('channel')
        if channel is not None:
            for item in channel.findall('item'):
                items.append({
                    'title': (item.findtext('title') or '').strip(),
                    'link': (item.findtext('link') or '').strip(),
                    'description': (item.findtext('description') or '').strip(),
                    'published': (item.findtext('pubDate') or '').strip(),
                })

    return items


def parse_date(date_str: str) -> datetime | None:
    """Parse an RFC 2822 or ISO 8601 date string."""
    if not date_str:
        return None
    for fmt in (
        "%a, %d %b %Y %H:%M:%S %z",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%d %H:%M:%S",
    ):
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    return None


def main():
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(hours=24)

    workspace = Path("/home/node/.openclaw/workspace")
    output = workspace / "reports/daily/the-register-daily.md"

    lines = [f"# The Register Digest — {now.strftime('%Y-%m-%d %A')} UTC\n"]

    for feed in FEEDS:
        lines.append(f"## {feed['name']}\n")
        try:
            raw_items = fetch_feed(feed["url"])
        except Exception as e:
            lines.append(f"_Error fetching feed: {e}_\n")
            continue

        recent = []
        for item in raw_items:
            dt = parse_date(item.get("published", ""))
            if dt and dt >= cutoff:
                recent.append(item)

        if not recent:
            lines.append("_No recent items in this feed._\n")
            continue

        # Sort newest first
        recent.sort(
            key=lambda i: parse_date(i.get("published", "")) or datetime.min.replace(tzinfo=timezone.utc),
            reverse=True,
        )

        for item in recent:
            headline = unescape(item["title"])
            desc = strip_html(unescape(item["description"]))
            pub = item.get("published", "Unknown time")
            link = item.get("link", "")

            lines.append(f"- **{headline}**")
            if desc:
                lines.append(f"  - {desc}")
            lines.append(f"  - _Published: {pub}_")
            if link:
                lines.append(f"  - [Link]({link})")
            lines.append("")

    report = "\n".join(lines)
    output.write_text(report, encoding="utf-8")
    print(f"Report saved to {output}")


if __name__ == "__main__":
    main()
