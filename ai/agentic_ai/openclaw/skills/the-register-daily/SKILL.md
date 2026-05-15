---
name: the-register-daily
description: Fetch The Register RSS feeds for AI/ML and Offbeat, filter to last 24 hours, and generate a curated news report. Use when asked to run the daily Register digest, check The Register for recent articles, or fetch their RSS feeds manually.
---

# The Register Daily Digest

Fetch two RSS feeds from The Register, filter to the last 24 hours, and save a markdown report.

## Usage

Run the bundled script:

```bash
python3 <skill-dir>/scripts/the-register-daily.py
```

The script writes the report to `/home/node/.openclaw/workspace/reports/daily/the-register-daily.md` with today's date as the header.

## Feeds

1. **AI & ML**: `https://api.theregister.com/api/v1/article?query=tag:"ai and ml"&orderBy=published&site_id=2&remapper=rss`
2. **Offbeat**: `https://api.theregister.com/api/v1/article?query=tag:offbeat&orderBy=published&site_id=2&remapper=rss`

## Output

Each report includes:
- Headline
- Brief 1-2 sentence summary (or headline-only if no description)
- Source feed name
- Published time

Grouped by feed. Notes if a feed returned no recent items.
