---
name: fengye-markdown-fetch
description: "Fetch any web page and convert to clean Markdown. Supports multiple providers with automatic fallback: Jina Reader (r.jina.ai), Defuddle (defuddle.md), and raw HTML conversion. Use for saving articles, blog posts, documentation, or any web content."
---

# fengye-markdown-fetch

Fetch any web page and convert it to clean Markdown, with multiple providers and automatic fallback.

## When to Use

Use this skill when the user wants to:
- Fetch a web article or blog post as Markdown
- Save or archive web content
- Convert any URL to readable Markdown
- Get clean text from a web page

**Note:** For X/Twitter posts, use `fengye-x-fetch` instead — it uses X's GraphQL API for much better results.

## Providers

The script supports 3 providers, tried in order by default:

| Priority | Provider | API | Best For |
|----------|----------|-----|----------|
| 1 | **Jina Reader** | `r.jina.ai` | General articles, JS-rendered pages |
| 2 | **Defuddle** | `defuddle.md` | Blog posts, clean extraction with frontmatter |
| 3 | **Raw** | `requests + html2text` | Fallback when proxies fail |

### Jina Reader
- Free, no API key
- Handles JavaScript-rendered pages (server-side rendering)
- Good at stripping navigation, ads, sidebars
- Rate limited but sufficient for personal use

### Defuddle
- By the Obsidian team
- Returns YAML frontmatter (title, author, date, etc.)
- Excellent content extraction quality
- Good for structured articles

### Raw (html2text)
- Direct HTML fetch + conversion
- Works when proxy services are down
- Requires `html2text` package for best results
- Won't handle JS-rendered content

## Prerequisites

```bash
pip install requests
pip install html2text  # optional, improves raw provider
```

## Usage

### Auto mode (recommended)

```bash
python <skill-path>/scripts/fetch_markdown.py "https://example.com/article"
```

Tries Jina → Defuddle → Raw, picks the best result.

### Specific provider

```bash
python <skill-path>/scripts/fetch_markdown.py "https://example.com/article" --provider jina
python <skill-path>/scripts/fetch_markdown.py "https://example.com/article" --provider defuddle
python <skill-path>/scripts/fetch_markdown.py "https://example.com/article" --provider raw
```

### JSON output

```bash
python <skill-path>/scripts/fetch_markdown.py "https://example.com/article" --json
```

Returns:
```json
{
  "provider": "jina",
  "title": "Article Title",
  "content": "# Article Title\n\nArticle body...",
  "url": "https://example.com/article",
  "content_length": 4523
}
```

### Custom timeout

```bash
python <skill-path>/scripts/fetch_markdown.py "https://slow-site.com/page" --timeout 60
```

### Download media (images/video/audio)

Download all media referenced in the article to a local directory. URLs in the Markdown output are automatically replaced with local paths.

```bash
python <skill-path>/scripts/fetch_markdown.py "https://example.com/article" --download-media ./assets
```

Combine with other flags:
```bash
python <skill-path>/scripts/fetch_markdown.py "https://example.com/article" --download-media ./assets --json
```

**Behavior:**
- Downloads images (`![](url)`), videos, audio from `<img>`, `<video>`, `<audio>`, `<source>` tags
- Filenames: `{basename}-{hash8}.{ext}` (deterministic, dedup-safe)
- Failed downloads keep their original URL
- Skips non-media responses (HTML error pages)

## URL Routing Guide

| URL Pattern | Recommended Tool |
|-------------|-----------------|
| `x.com/*` or `twitter.com/*` | Use `fengye-x-fetch` skill |
| General web articles | This skill (auto mode) |
| GitHub repos | This skill or `fetch_webpage` tool |
| Docs/MDN/Wikipedia | This skill (Jina works great) |

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Jina returns short content | Try `--provider defuddle` |
| Both proxies fail | Try `--provider raw` (needs direct access) |
| Rate limited by Jina | Wait a minute, or use defuddle |
| JS-heavy SPA returns empty | Jina handles this; defuddle may not |
| Paywall content | None of these can bypass paywalls |
