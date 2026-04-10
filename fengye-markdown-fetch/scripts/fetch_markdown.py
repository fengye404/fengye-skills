#!/usr/bin/env python3
"""
Fetch any web page and convert it to clean Markdown.

Uses multiple providers with automatic fallback:
  1. Jina Reader  (r.jina.ai)
  2. Defuddle     (defuddle.md)
  3. Raw fetch    (requests + html2text)

Usage:
    python fetch_markdown.py <url> [--provider jina|defuddle|raw|auto] [--json] [--timeout 30]

Examples:
    python fetch_markdown.py https://example.com/article
    python fetch_markdown.py https://example.com/article --provider defuddle
    python fetch_markdown.py https://example.com/article --json
"""

import argparse
import json
import re
import sys
import time
from typing import Optional

try:
    import requests
except ImportError:
    print("Error: 'requests' package is required. Install with: pip install requests", file=sys.stderr)
    sys.exit(1)

UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/131.0.0.0 Safari/537.36"
)


# ── Providers ──────────────────────────────────────────────────────────────────

def fetch_via_jina(url: str, timeout: int = 30) -> dict:
    """Fetch via Jina Reader (r.jina.ai).

    Returns clean Markdown. Free, no API key needed.
    Handles JS-rendered pages server-side.
    """
    api_url = f"https://r.jina.ai/{url}"
    headers = {
        "Accept": "text/markdown",
        "User-Agent": UA,
    }

    resp = requests.get(api_url, headers=headers, timeout=timeout)
    resp.raise_for_status()

    content = resp.text
    title, body = _split_jina_response(content)

    return {
        "provider": "jina",
        "title": title,
        "content": body,
        "url": url,
        "content_length": len(body),
    }


def _split_jina_response(text: str) -> tuple:
    """Parse Jina Reader response which has Title: and URL: header lines."""
    lines = text.split("\n")
    title = ""
    start = 0

    for i, line in enumerate(lines):
        if line.startswith("Title:"):
            title = line[6:].strip()
        elif line.startswith("URL:"):
            continue
        elif line.startswith("Markdown Content:"):
            start = i + 1
            break
        elif title and line.strip() == "":
            start = i + 1
            break

    # If no header found, try extracting title from first # heading
    body = "\n".join(lines[start:]).strip()
    if not title:
        m = re.search(r"^#\s+(.+)$", body, re.MULTILINE)
        if m:
            title = m.group(1).strip()

    return title, body


def fetch_via_defuddle(url: str, timeout: int = 30) -> dict:
    """Fetch via Defuddle (defuddle.md).

    Returns Markdown with YAML frontmatter.
    Made by Obsidian team, good content extraction.
    """
    # Defuddle expects URL without protocol prefix
    clean_url = re.sub(r"^https?://", "", url)
    api_url = f"https://defuddle.md/{clean_url}"

    resp = requests.get(api_url, timeout=timeout, headers={"User-Agent": UA})
    resp.raise_for_status()

    content = resp.text
    title, body = _split_frontmatter(content)

    return {
        "provider": "defuddle",
        "title": title,
        "content": body if body else content,
        "url": url,
        "content_length": len(body if body else content),
    }


def _split_frontmatter(text: str) -> tuple:
    """Extract title from YAML frontmatter and return (title, body)."""
    title = ""
    body = text

    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            frontmatter = parts[1]
            body = parts[2].strip()
            # Extract title from frontmatter
            for line in frontmatter.split("\n"):
                if line.strip().startswith("title:"):
                    title = line.split(":", 1)[1].strip().strip('"').strip("'")
                    break

    if not title:
        m = re.search(r"^#\s+(.+)$", body, re.MULTILINE)
        if m:
            title = m.group(1).strip()

    return title, body


def fetch_via_raw(url: str, timeout: int = 30) -> dict:
    """Fetch raw HTML and convert to Markdown using html2text.

    Fallback when proxy services are unavailable.
    """
    try:
        import html2text
    except ImportError:
        print("Warning: html2text not installed. Install with: pip install html2text", file=sys.stderr)
        # Simple fallback: just strip tags
        resp = requests.get(url, timeout=timeout, headers={"User-Agent": UA})
        resp.raise_for_status()
        text = re.sub(r"<[^>]+>", "", resp.text)
        text = re.sub(r"\s+", " ", text).strip()
        return {
            "provider": "raw-strip",
            "title": "",
            "content": text[:5000],
            "url": url,
            "content_length": len(text),
        }

    resp = requests.get(url, timeout=timeout, headers={"User-Agent": UA})
    resp.raise_for_status()

    h = html2text.HTML2Text()
    h.ignore_links = False
    h.ignore_images = False
    h.body_width = 0  # No wrapping
    h.ignore_emphasis = False

    content = h.handle(resp.text)

    # Try to extract title from HTML
    title = ""
    title_match = re.search(r"<title[^>]*>([^<]+)</title>", resp.text, re.IGNORECASE)
    if title_match:
        title = title_match.group(1).strip()

    return {
        "provider": "raw",
        "title": title,
        "content": content,
        "url": url,
        "content_length": len(content),
    }


# ── Auto mode: try providers in order ─────────────────────────────────────────

PROVIDERS = {
    "jina": fetch_via_jina,
    "defuddle": fetch_via_defuddle,
    "raw": fetch_via_raw,
}

PROVIDER_ORDER = ["jina", "defuddle", "raw"]


def fetch_auto(url: str, timeout: int = 30) -> dict:
    """Try providers in order, return the first successful result.

    Also compares results if multiple succeed to pick the best one.
    """
    results = []
    errors = []

    for name in PROVIDER_ORDER:
        try:
            print(f"Trying {name}...", file=sys.stderr)
            result = PROVIDERS[name](url, timeout)
            if result["content_length"] > 100:
                results.append(result)
                print(f"  {name}: OK ({result['content_length']} chars, title: {result['title'][:50]})", file=sys.stderr)
                # If we got a good result from a proxy, no need for raw
                if name in ("jina", "defuddle") and result["content_length"] > 500:
                    break
            else:
                print(f"  {name}: Too short ({result['content_length']} chars), trying next", file=sys.stderr)
        except Exception as e:
            errors.append({"provider": name, "error": str(e)})
            print(f"  {name}: Failed ({e})", file=sys.stderr)

    if not results:
        print("Error: All providers failed.", file=sys.stderr)
        for err in errors:
            print(f"  {err['provider']}: {err['error']}", file=sys.stderr)
        sys.exit(1)

    # Pick the best result (longest content)
    best = max(results, key=lambda r: r["content_length"])
    return best


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Fetch web page content as clean Markdown"
    )
    parser.add_argument("url", help="URL to fetch")
    parser.add_argument(
        "--provider", choices=["jina", "defuddle", "raw", "auto"],
        default="auto",
        help="Content provider (default: auto, tries all in order)"
    )
    parser.add_argument(
        "--json", action="store_true",
        help="Output as JSON with metadata"
    )
    parser.add_argument(
        "--timeout", type=int, default=30,
        help="Request timeout in seconds (default: 30)"
    )

    args = parser.parse_args()

    if args.provider == "auto":
        result = fetch_auto(args.url, args.timeout)
    else:
        try:
            result = PROVIDERS[args.provider](args.url, args.timeout)
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        # Output markdown with title header if available
        if result["title"]:
            print(f"# {result['title']}\n")
            print(f"**Source:** {result['url']}")
            print(f"**Provider:** {result['provider']}")
            print()
            print("---")
            print()
        print(result["content"])


if __name__ == "__main__":
    main()
