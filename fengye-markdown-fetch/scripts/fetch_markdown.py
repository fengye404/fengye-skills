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
import hashlib
import json
import os
import re
import sys
import time
import urllib.parse
from pathlib import Path
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


# ── Media Download ─────────────────────────────────────────────────────────────

# Patterns to match media URLs in Markdown
_MD_IMAGE_RE = re.compile(r'(!\[[^\]]*\])\((\s*https?://[^)]+)\)')
_MD_LINK_RE = re.compile(r'(\[[^\]]*\])\((\s*https?://[^)]+)\)')
_HTML_MEDIA_RE = re.compile(
    r'(<(?:img|video|audio|source)\b[^>]*?\b(?:src|poster)=["\'])(https?://[^"\']+)(["\'])',
    re.IGNORECASE,
)

# URL patterns that are known media hosts (download even without media extension)
_KNOWN_MEDIA_HOSTS = {
    "pbs.twimg.com",
    "video.twimg.com",
    "i.imgur.com",
    "media.giphy.com",
}

# Extensions considered as media
_MEDIA_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg", ".bmp", ".ico", ".avif",
    ".mp4", ".webm", ".mov", ".avi", ".mkv",
    ".mp3", ".wav", ".ogg", ".flac", ".aac", ".m4a",
}


def _is_media_url(url: str) -> bool:
    """Check if a URL points to a media file (by extension or known host)."""
    parsed = urllib.parse.urlparse(url)
    ext = Path(parsed.path).suffix.lower()
    if ext in _MEDIA_EXTENSIONS:
        return True
    if parsed.hostname in _KNOWN_MEDIA_HOSTS:
        return True
    return False


def _upgrade_media_url(url: str) -> str:
    """Upgrade media URLs to get original quality where possible.

    - X/Twitter images: append ?name=orig for full resolution
    """
    parsed = urllib.parse.urlparse(url)
    if parsed.hostname == "pbs.twimg.com" and "/media/" in parsed.path:
        qs = urllib.parse.parse_qs(parsed.query)
        if qs.get("name", [None])[0] != "orig":
            qs["name"] = ["orig"]
            new_query = urllib.parse.urlencode(qs, doseq=True)
            return urllib.parse.urlunparse(parsed._replace(query=new_query))
    return url


# Content-Type to extension mapping
_CONTENT_TYPE_EXT = {
    "image/jpeg": ".jpg", "image/png": ".png", "image/gif": ".gif",
    "image/webp": ".webp", "image/svg+xml": ".svg", "image/avif": ".avif",
    "video/mp4": ".mp4", "video/webm": ".webm", "video/quicktime": ".mov",
    "audio/mpeg": ".mp3", "audio/wav": ".wav", "audio/ogg": ".ogg",
    "audio/flac": ".flac", "audio/aac": ".aac", "audio/mp4": ".m4a",
}


def _ext_from_url(url: str) -> str:
    """Extract media extension from URL, checking both path and query params."""
    parsed = urllib.parse.urlparse(url)
    ext = Path(parsed.path).suffix.lower()
    ext = re.sub(r"\?.*", "", ext)
    if ext in _MEDIA_EXTENSIONS:
        return ext
    # Check ?format= query param (X/Twitter style)
    qs = urllib.parse.parse_qs(parsed.query)
    fmt = qs.get("format", [None])[0]
    if fmt:
        candidate = f".{fmt.lower()}"
        if candidate in _MEDIA_EXTENSIONS:
            return candidate
    return ""


def _url_to_filename(url: str, content_type: str = "") -> str:
    """Generate a deterministic filename from URL: basename-hash8.ext"""
    parsed = urllib.parse.urlparse(url)
    path_part = Path(parsed.path)

    # Try extension from URL, then content-type, then default
    ext = _ext_from_url(url)
    if not ext and content_type:
        base_ct = content_type.split(";")[0].strip().lower()
        ext = _CONTENT_TYPE_EXT.get(base_ct, "")
    if not ext:
        ext = ".jpg"  # safe default

    # Get basename (without extension)
    stem = path_part.stem or "media"
    stem = re.sub(r"[^\w\-]", "-", stem)[:60]  # sanitize, truncate

    # 8-char hash for uniqueness
    url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
    return f"{stem}-{url_hash}{ext}"


def download_media_in_markdown(markdown: str, output_dir: str) -> str:
    """Download all media referenced in markdown, replace URLs with local paths.

    Handles:
      - Markdown images: ![alt](https://...)
      - HTML media tags: <img src="...">, <video src="...">, <audio src="...">, <source src="...">

    Returns the markdown with URLs replaced by local relative paths.
    Failed downloads keep their original URL.
    """
    os.makedirs(output_dir, exist_ok=True)
    downloaded = {}  # url -> local_filename (cache for dedup)
    count = 0

    def _download(url: str) -> Optional[str]:
        """Download a single URL, return local filename or None on failure."""
        nonlocal count
        url = url.strip()
        url = _upgrade_media_url(url)
        if url in downloaded:
            return downloaded[url]

        try:
            resp = requests.get(url, timeout=30, headers={"User-Agent": UA})
            resp.raise_for_status()
            content_type = resp.headers.get("content-type", "")
            # Skip non-media responses (HTML error pages etc.)
            if "text/html" in content_type and not url.endswith(".svg"):
                print(f"  Skipped (HTML response): {url}", file=sys.stderr)
                downloaded[url] = None
                return None
            filename = _url_to_filename(url, content_type)
            local_path = os.path.join(output_dir, filename)
            with open(local_path, "wb") as f:
                f.write(resp.content)
            count += 1
            print(f"  Downloaded: {filename}", file=sys.stderr)
            downloaded[url] = filename
            return filename
        except Exception as e:
            print(f"  Failed: {url} ({e})", file=sys.stderr)
            downloaded[url] = None
            return None

    def _replace_md(m):
        prefix, url = m.group(1), m.group(2).strip()
        filename = _download(url)
        if filename:
            return f"{prefix}({output_dir}/{filename})"
        return m.group(0)

    def _replace_md_link(m):
        prefix, url = m.group(1), m.group(2).strip()
        if _is_media_url(url):
            filename = _download(url)
            if filename:
                return f"{prefix}({output_dir}/{filename})"
        return m.group(0)

    def _replace_html(m):
        prefix, url, suffix = m.group(1), m.group(2), m.group(3)
        filename = _download(url)
        if filename:
            return f"{prefix}{output_dir}/{filename}{suffix}"
        return m.group(0)

    result = _MD_IMAGE_RE.sub(_replace_md, markdown)
    result = _MD_LINK_RE.sub(_replace_md_link, result)
    result = _HTML_MEDIA_RE.sub(_replace_html, result)

    print(f"  Media: {count} downloaded, {sum(1 for v in downloaded.values() if v is None)} failed/skipped", file=sys.stderr)
    return result


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
    parser.add_argument(
        "--download-media", metavar="DIR",
        help="Download all media (images/video/audio) to DIR, replace URLs with local paths"
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
        if args.download_media:
            result["content"] = download_media_in_markdown(result["content"], args.download_media)
            result["content_length"] = len(result["content"])
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        content = result["content"]
        if args.download_media:
            content = download_media_in_markdown(content, args.download_media)
        # Output markdown with title header if available
        if result["title"]:
            print(f"# {result['title']}\n")
            print(f"**Source:** {result['url']}")
            print(f"**Provider:** {result['provider']}")
            print()
            print("---")
            print()
        print(content)


if __name__ == "__main__":
    main()
