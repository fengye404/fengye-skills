#!/usr/bin/env python3
"""
Fetch X/Twitter post content via internal GraphQL API.
Inspired by RSSHub's Twitter route implementation.

Usage:
    python fetch_tweet.py <url_or_tweet_id> [--full-article] [--json] [--download-media <dir>]

Environment:
    X_AUTH_TOKEN  - Your X auth_token cookie value (required)
                    Resolved from: env var > .env file (~/.env or ./.env)

Examples:
    python fetch_tweet.py https://x.com/user/status/1234567890
    python fetch_tweet.py 1234567890 --full-article
    python fetch_tweet.py https://x.com/user/status/1234567890 --json
    python fetch_tweet.py https://x.com/user/status/1234567890 --download-media ./assets
    # --download-media downloads all images/video/audio and replaces URLs in output
"""

import argparse
import json
import os
import re
import sys
import urllib.parse
import hashlib
import time
from pathlib import Path
from typing import Dict, List, Optional

try:
    import requests
except ImportError:
    print("Error: 'requests' package is required. Install with: pip install requests", file=sys.stderr)
    sys.exit(1)


# ── Constants ──────────────────────────────────────────────────────────────────

# This bearer token is embedded in X's public JavaScript bundles.
# It is NOT a secret — it's the same for all users and used to identify the
# "Twitter for Web" client application.
BEARER_TOKEN = (
    "Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs"
    "%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA"
)

GRAPHQL_BASE = "https://x.com/i/api/graphql"

# Fallback query IDs — used when dynamic resolution fails
FALLBACK_QUERY_IDS = {
    "TweetDetail": "QuBlQ6SxNAQCt6-kBiCXCQ",
    "TweetResultByRestId": "V3vfsYzNEyD9tsf4xoFRgw",
}

# Cache file for resolved query IDs
QUERY_ID_CACHE = os.path.join(os.path.dirname(__file__), ".query_id_cache.json")


def resolve_query_ids() -> dict:
    """Dynamically resolve GraphQL query IDs from X's JS bundles.

    X rotates these IDs periodically. This function:
    1. Checks a local cache file (valid for 24h)
    2. Fetches https://x.com to find the main.js bundle URL
    3. Extracts query IDs from the JS bundle via regex
    4. Falls back to hardcoded IDs if all else fails
    """
    # ── Check cache ──
    if os.path.exists(QUERY_ID_CACHE):
        try:
            with open(QUERY_ID_CACHE) as f:
                cached = json.load(f)
            # Cache valid for 24 hours
            if time.time() - cached.get("_ts", 0) < 86400:
                ids = {k: v for k, v in cached.items() if not k.startswith("_")}
                if ids:
                    print("Using cached query IDs", file=sys.stderr)
                    return ids
        except (json.JSONDecodeError, IOError):
            pass

    # ── Fetch from X's JS bundles ──
    print("Resolving fresh query IDs from X...", file=sys.stderr)
    try:
        # Step 1: Get the X homepage to find main.js URL
        resp = requests.get("https://x.com", timeout=15, headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/131.0.0.0 Safari/537.36",
        })
        resp.raise_for_status()

        # Step 2: Find the main JS bundle URL
        # Pattern: /client-web/main.HASH.js or similar
        main_match = re.search(
            r'(?:href|src)=["\']([^"\']*?/client-web(?:-canary)?/main\.[a-z0-9]+[a-z]\.[a-z0-9]+\.js)["\']',
            resp.text
        )
        if not main_match:
            # Try alternative pattern
            main_match = re.search(r'/client-web/main\.([a-z0-9]+)\.', resp.text)
            if main_match:
                main_url = f"https://abs.twimg.com/responsive-web/client-web/main.{main_match.group(1)}.js"
            else:
                print("Could not find main.js URL, using fallback IDs", file=sys.stderr)
                return dict(FALLBACK_QUERY_IDS)
        else:
            main_url = main_match.group(1)
            if main_url.startswith("/"):
                main_url = "https://x.com" + main_url

        # Step 3: Fetch the JS bundle and extract query IDs
        print(f"Fetching JS bundle...", file=sys.stderr)
        js_resp = requests.get(main_url, timeout=30, headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/131.0.0.0 Safari/537.36",
        })
        js_resp.raise_for_status()

        # Extract queryId:"xxx"...operationName:"yyy" patterns
        ids = {}
        for match in re.finditer(
            r'queryId:"([^"]+?)".+?operationName:"([^"]+?)"',
            js_resp.text
        ):
            query_id, operation_name = match.group(1), match.group(2)
            if operation_name in ("TweetDetail", "TweetResultByRestId",
                                  "UserTweets", "UserByScreenName"):
                ids[operation_name] = query_id

        if ids:
            print(f"Resolved {len(ids)} query IDs: {list(ids.keys())}", file=sys.stderr)
            # Save to cache
            cache_data = {**ids, "_ts": time.time()}
            try:
                with open(QUERY_ID_CACHE, "w") as f:
                    json.dump(cache_data, f)
            except IOError:
                pass
            # Merge with fallbacks for any missing operations
            return {**FALLBACK_QUERY_IDS, **ids}

        print("No query IDs found in JS bundle, using fallback", file=sys.stderr)
        return dict(FALLBACK_QUERY_IDS)

    except Exception as e:
        print(f"Failed to resolve query IDs: {e}. Using fallback.", file=sys.stderr)
        return dict(FALLBACK_QUERY_IDS)


# Feature flags required by the GraphQL API
TWEET_DETAIL_FEATURES = {
    "rweb_tipjar_consumption_enabled": True,
    "responsive_web_graphql_exclude_directive_enabled": True,
    "verified_phone_label_enabled": False,
    "creator_subscriptions_tweet_preview_api_enabled": True,
    "responsive_web_graphql_timeline_navigation_enabled": True,
    "responsive_web_graphql_skip_user_profile_image_extensions_enabled": False,
    "communities_web_enable_tweet_community_results_fetch": True,
    "c9s_tweet_anatomy_moderator_badge_enabled": True,
    "articles_preview_enabled": True,
    "responsive_web_edit_tweet_api_enabled": True,
    "graphql_is_translatable_rweb_tweet_is_translatable_enabled": True,
    "view_counts_everywhere_api_enabled": True,
    "longform_notetweets_consumption_enabled": True,
    "responsive_web_twitter_article_tweet_consumption_enabled": True,
    "tweet_awards_web_tipping_enabled": False,
    "creator_subscriptions_quote_tweet_preview_enabled": False,
    "freedom_of_speech_not_reach_fetch_enabled": True,
    "standardized_nudges_misinfo": True,
    "tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled": True,
    "rweb_video_timestamps_enabled": True,
    "longform_notetweets_rich_text_read_enabled": True,
    "longform_notetweets_inline_media_enabled": True,
    "responsive_web_enhance_cards_enabled": False,
}


# ── API Client ─────────────────────────────────────────────────────────────────

class XApiClient:
    """Client for X's internal GraphQL API using auth_token cookie."""

    def __init__(self, auth_token: str):
        self.auth_token = auth_token
        self.session = requests.Session()
        self.csrf_token = None
        self.query_ids = resolve_query_ids()
        self._setup_session()

    def _setup_session(self):
        """Configure session with cookies and headers.

        Fetches a real ct0 (CSRF token) from X by visiting the homepage
        with the auth_token cookie. Self-generated ct0 values are rejected
        by some endpoints (notably TweetDetail returns 403).
        """
        self.session.cookies.set("auth_token", self.auth_token, domain=".x.com")

        # Fetch real ct0 from X
        print("Authenticating with X...", file=sys.stderr)
        try:
            resp = self.session.get("https://x.com", timeout=15, headers={
                "User-Agent": (
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/131.0.0.0 Safari/537.36"
                ),
            })
            resp.raise_for_status()
            self.csrf_token = self.session.cookies.get("ct0", domain=".x.com")
        except Exception as e:
            print(f"Warning: Could not fetch ct0 from X: {e}", file=sys.stderr)

        if not self.csrf_token:
            # Fallback: generate our own ct0 (works for some endpoints)
            print("Warning: Using self-generated ct0 (some endpoints may reject it)", file=sys.stderr)
            self.csrf_token = hashlib.md5(
                f"{self.auth_token}{time.time()}".encode()
            ).hexdigest()
            self.session.cookies.set("ct0", self.csrf_token, domain=".x.com")

        self.session.headers.update({
            "authority": "x.com",
            "accept": "*/*",
            "accept-language": "en-US,en;q=0.9",
            "authorization": BEARER_TOKEN,
            "content-type": "application/json",
            "dnt": "1",
            "referer": "https://x.com/",
            "user-agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/131.0.0.0 Safari/537.36"
            ),
            "x-twitter-active-user": "yes",
            "x-twitter-client-language": "en",
            "x-csrf-token": self.csrf_token,
            "x-twitter-auth-type": "OAuth2Session",
        })

    def fetch_tweet_detail(self, tweet_id: str) -> dict:
        """Fetch full tweet detail via TweetDetail GraphQL endpoint."""
        variables = {
            "focalTweetId": tweet_id,
            "with_rux_injections": False,
            "includePromotedContent": False,
            "withCommunity": True,
            "withQuickPromoteEligibilityTweetFields": True,
            "withBirdwatchNotes": True,
            "withVoice": True,
            "withV2Timeline": True,
        }

        field_toggles = {
            "withArticleRichContentState": True,
            "withArticlePlainText": True,
        }

        params = {
            "variables": json.dumps(variables, separators=(",", ":")),
            "features": json.dumps(TWEET_DETAIL_FEATURES, separators=(",", ":")),
            "fieldToggles": json.dumps(field_toggles, separators=(",", ":")),
        }

        url = f"{GRAPHQL_BASE}/{self.query_ids['TweetDetail']}/TweetDetail"
        resp = self.session.get(url, params=params, timeout=30)

        if resp.status_code == 404:
            # Query ID may be stale — clear cache and retry once
            if os.path.exists(QUERY_ID_CACHE):
                os.remove(QUERY_ID_CACHE)
                print("Query ID stale (404). Clearing cache and retrying...", file=sys.stderr)
                self.query_ids = resolve_query_ids()
                url = f"{GRAPHQL_BASE}/{self.query_ids['TweetDetail']}/TweetDetail"
                resp = self.session.get(url, params=params, timeout=30)

        if resp.status_code == 401:
            print("Error: Authentication failed. Your X_AUTH_TOKEN may be expired.", file=sys.stderr)
            sys.exit(1)
        if resp.status_code == 429:
            print("Error: Rate limited. Try again later.", file=sys.stderr)
            sys.exit(1)

        resp.raise_for_status()
        return resp.json()


# ── Response Parser ────────────────────────────────────────────────────────────

def extract_tweet_id(url_or_id: str) -> str:
    """Extract tweet ID from a URL or return as-is if already an ID."""
    if url_or_id.isdigit():
        return url_or_id

    # Match patterns like:
    #   https://x.com/user/status/1234567890
    #   https://twitter.com/user/status/1234567890
    #   https://x.com/user/status/1234567890?s=20
    match = re.search(r"(?:twitter\.com|x\.com)/\w+/status/(\d+)", url_or_id)
    if match:
        return match.group(1)

    print(f"Error: Cannot extract tweet ID from: {url_or_id}", file=sys.stderr)
    sys.exit(1)


def find_tweet_in_response(data: dict, tweet_id: str) -> Optional[dict]:
    """Navigate the deeply nested response to find the target tweet."""
    try:
        instructions = data["data"]["threaded_conversation_with_injections_v2"]["instructions"]
    except (KeyError, TypeError):
        return None

    for instruction in instructions:
        if instruction.get("type") != "TimelineAddEntries":
            continue
        for entry in instruction.get("entries", []):
            entry_id = entry.get("entryId", "")
            if not entry_id.startswith(f"tweet-{tweet_id}"):
                continue

            content = entry.get("content", {})
            item_content = content.get("itemContent", {})
            tweet_results = item_content.get("tweet_results", {})
            result = tweet_results.get("result", {})

            # Empty tweet_results means restricted/unavailable content
            if not result:
                return None

            # Handle "TweetWithVisibilityResults" wrapper
            if result.get("__typename") == "TweetWithVisibilityResults":
                result = result.get("tweet", result)

            return result

    return None


def parse_tweet(tweet: dict, include_article: bool = False) -> dict:
    """Parse raw tweet object into a clean structure."""
    legacy = tweet.get("legacy", {})
    core = tweet.get("core", {})
    user_result = core.get("user_results", {}).get("result", {})

    # X changed user data structure: legacy.name → core.name, legacy.profile_image_url_https → avatar.image_url
    # Support both old and new formats
    user_legacy = user_result.get("legacy", {})
    user_core = user_result.get("core", {})
    user_avatar = user_result.get("avatar", {})

    author_name = user_core.get("name") or user_legacy.get("name", "")
    author_screen_name = user_core.get("screen_name") or user_legacy.get("screen_name", "")
    author_avatar = (
        user_avatar.get("image_url")
        or user_legacy.get("profile_image_url_https", "")
    ).replace("_normal", "")

    # ── Text ──
    text = legacy.get("full_text", "")

    # Check for note_tweet (X Articles / long posts)
    note_tweet = tweet.get("note_tweet", {}).get("note_tweet_results", {}).get("result", {})
    if note_tweet:
        article_text = note_tweet.get("text", "")
        if article_text:
            if include_article:
                text = article_text
            else:
                # Still include a hint
                text = article_text

    # ── Media ──
    media_list = []
    extended_entities = legacy.get("extended_entities", {})
    for media in extended_entities.get("media", []):
        media_type = media.get("type", "photo")
        # Always request original quality for photos
        photo_url = media.get("media_url_https", "")
        if media_type == "photo" and photo_url and "?" not in photo_url:
            photo_url = f"{photo_url}?name=orig"
        entry = {
            "type": media_type,
            "url": photo_url,
            "alt_text": media.get("ext_alt_text", ""),
        }
        if media_type in ("video", "animated_gif"):
            variants = media.get("video_info", {}).get("variants", [])
            # Pick highest bitrate MP4
            mp4s = [v for v in variants if v.get("content_type") == "video/mp4"]
            if mp4s:
                best = max(mp4s, key=lambda v: v.get("bitrate", 0))
                entry["video_url"] = best["url"]
        media_list.append(entry)

    # ── URLs ── expand t.co links
    entities = legacy.get("entities", {})
    urls_map = {}
    for url_entity in entities.get("urls", []):
        short = url_entity.get("url", "")
        expanded = url_entity.get("expanded_url", short)
        urls_map[short] = expanded

    for short, expanded in urls_map.items():
        text = text.replace(short, expanded)

    # Remove trailing media t.co links
    text = re.sub(r"\s*https://t\.co/\w+$", "", text)

    # ── X Article (standalone long-form content) ──
    article_data = tweet.get("article", {}).get("article_results", {}).get("result", {})
    x_article = None
    if article_data and include_article:
        # Build mediaId → URL mapping
        media_id_to_url = {}
        media_list_article = []
        for me in article_data.get("media_entities", []):
            mi = me.get("media_info", {})
            if mi.get("__typename") == "ApiImage":
                img_url = mi.get("original_img_url", "")
                mid = str(me.get("media_id", ""))
                if img_url:
                    media_list_article.append({"type": "photo", "url": img_url, "alt_text": ""})
                    if mid:
                        media_id_to_url[mid] = img_url

        x_article = {
            "title": article_data.get("title", ""),
            "plain_text": article_data.get("plain_text", ""),
            "preview_text": article_data.get("preview_text", ""),
            "media": media_list_article,
            "content_state": article_data.get("content_state", None),
            "media_id_to_url": media_id_to_url,
        }

    # ── Quoted tweet ──
    quoted = None
    quoted_result = tweet.get("quoted_status_result", {}).get("result", {})
    if quoted_result and quoted_result.get("__typename") in ("Tweet", "TweetWithVisibilityResults"):
        if quoted_result.get("__typename") == "TweetWithVisibilityResults":
            quoted_result = quoted_result.get("tweet", quoted_result)
        quoted = parse_tweet(quoted_result, include_article)

    # ── Conversation thread ──
    return {
        "id": legacy.get("id_str", tweet.get("rest_id", "")),
        "text": text,
        "author": {
            "name": author_name,
            "screen_name": author_screen_name,
            "avatar": author_avatar,
        },
        "created_at": legacy.get("created_at", ""),
        "media": media_list,
        "quoted_tweet": quoted,
        "retweet_count": legacy.get("retweet_count", 0),
        "like_count": legacy.get("favorite_count", 0),
        "reply_count": legacy.get("reply_count", 0),
        "bookmark_count": legacy.get("bookmark_count", 0),
        "is_article": bool(note_tweet),
        "x_article": x_article,
        "lang": legacy.get("lang", ""),
    }


def find_thread_tweets(data: dict, tweet_id: str, author_screen_name: str) -> List[dict]:
    """Find conversation thread tweets (self-replies by same author above the focal tweet)."""
    thread = []
    try:
        instructions = data["data"]["threaded_conversation_with_injections_v2"]["instructions"]
    except (KeyError, TypeError):
        return thread

    for instruction in instructions:
        if instruction.get("type") != "TimelineAddEntries":
            continue
        for entry in instruction.get("entries", []):
            entry_id = entry.get("entryId", "")
            if not entry_id.startswith("tweet-"):
                continue

            # Skip the focal tweet itself
            this_id = entry_id.replace("tweet-", "")
            if this_id == tweet_id:
                continue

            content = entry.get("content", {})
            item_content = content.get("itemContent", {})
            tweet_results = item_content.get("tweet_results", {})
            result = tweet_results.get("result", {})

            if result.get("__typename") == "TweetWithVisibilityResults":
                result = result.get("tweet", result)

            # Only include tweets from the same author (thread)
            user_res = result.get("core", {}).get("user_results", {}).get("result", {})
            screen_name = (
                user_res.get("core", {}).get("screen_name")
                or user_res.get("legacy", {}).get("screen_name", "")
            )
            if screen_name.lower() == author_screen_name.lower():
                thread.append(result)

    return thread


# ── Draft.js Content State Renderer ────────────────────────────────────────────

def _apply_block_formatting(text: str, inline_style_ranges: list,
                            entity_ranges: list, entity_by_key: dict) -> str:
    """Apply inline styles and entity links to a Draft.js block's text.

    All operations use original text offsets and are applied from end to start.
    Links are prioritized: inline styles that fully overlap a link range
    wrap the link in markdown syntax.
    entity_by_key: dict mapping string key → entity object.
    """
    if not text:
        return text
    from collections import defaultdict

    # Collect link operations from entity_ranges
    link_ops = {}  # (offset, end) → url
    for er in (entity_ranges or []):
        key = str(er.get("key", ""))
        offset = er.get("offset", 0)
        length = er.get("length", 0)
        entity = entity_by_key.get(key)
        if entity:
            etype = entity.get("value", {}).get("type", entity.get("type", ""))
            edata = entity.get("value", {}).get("data", entity.get("data", {}))
            if etype == "LINK" and "url" in edata:
                link_ops[(offset, offset + length)] = edata["url"]

    # Collect style operations — group by (offset, end) → set of styles
    style_groups = defaultdict(set)
    for sr in (inline_style_ranges or []):
        offset = sr.get("offset", 0)
        length = sr.get("length", 0)
        style = sr.get("style", "")
        style_groups[(offset, offset + length)].add(style)

    # Build combined operations — sort by offset descending to preserve offsets
    ops = []  # (offset, end, op_type, data)
    # Links first — these replace text with [text](url)
    for (start, end), url in link_ops.items():
        ops.append((start, end, "link", url))

    # Styles — skip ranges fully inside a link (they'll be applied to the link text)
    for (start, end), styles in style_groups.items():
        # Check if this style range exactly matches or fully contains a link
        has_link_inside = any(
            ls <= start and le >= end or ls >= start and le <= end
            for (ls, le) in link_ops
        )
        if "Bold" in styles and "Italic" in styles:
            ops.append((start, end, "bold_italic", None))
        elif "Bold" in styles:
            ops.append((start, end, "bold", None))
        elif "Italic" in styles:
            ops.append((start, end, "italic", None))

    # Sort: offset descending, then style ops before link ops at same offset
    # This way: first we apply the link (innermost), then wrap with style (outermost)
    def sort_key(op):
        start, end, op_type, data = op
        # Higher offset first; at same offset, links first (they're inner)
        type_order = 0 if op_type == "link" else 1
        return (-start, type_order)

    ops.sort(key=sort_key)

    # Apply operations. Process from end to start.
    # When a style overlaps with a link at same range, apply link first, then style wraps it.
    applied_links = set()  # Track which ranges became links

    for start, end, op_type, data in ops:
        if end > len(text):
            continue
        segment = text[start:end]

        if op_type == "link":
            text = text[:start] + f"[{segment}]({data})" + text[end:]
            applied_links.add((start, end))
        elif op_type in ("bold", "italic", "bold_italic"):
            # If a link was already applied at this range, segment now includes [text](url)
            # Re-extract the current segment
            # Calculate actual end position accounting for any link expansion
            actual_segment = text[start:start + len(text) - (len(text) - end)]
            # Actually, since we process from end, if we already applied a link at the
            # same or overlapping range, the text has shifted. Just re-extract.
            # For styles that exactly match a link range, the segment now contains [text](url)
            if (start, end) in applied_links:
                # The link was applied, so text between start and end is now different
                # Find the actual end by searching for the end of the link
                # Simple approach: look for ](url) after start
                link_url = link_ops.get((start, end), "")
                link_end_marker = f"]({link_url})"
                marker_pos = text.find(link_end_marker, start)
                if marker_pos >= 0:
                    actual_end = marker_pos + len(link_end_marker)
                    segment = text[start:actual_end]
                else:
                    segment = text[start:end]
                    actual_end = end
            else:
                actual_end = end
                segment = text[start:actual_end]

            if op_type == "bold_italic":
                text = text[:start] + f"***{segment}***" + text[actual_end:]
            elif op_type == "bold":
                text = text[:start] + f"**{segment}**" + text[actual_end:]
            elif op_type == "italic":
                text = text[:start] + f"*{segment}*" + text[actual_end:]

    return text



def _render_draftjs_article(x_article: dict) -> str:
    """Render X Article content_state (Draft.js) to Markdown with images inline."""
    cs = x_article.get("content_state")
    media_id_to_url = x_article.get("media_id_to_url", {})

    if not cs:
        # Fallback to plain_text + images at end
        return None

    if isinstance(cs, str):
        cs = json.loads(cs)

    blocks = cs.get("blocks", [])
    raw_entity_map = cs.get("entityMap", [])

    # Build key → entity dict. entityMap can be a list of {key, value} or a dict.
    entity_by_key = {}
    if isinstance(raw_entity_map, list):
        for item in raw_entity_map:
            k = str(item.get("key", ""))
            entity_by_key[k] = item
    elif isinstance(raw_entity_map, dict):
        for k, v in raw_entity_map.items():
            entity_by_key[str(k)] = v

    lines = []
    prev_was_list = False

    for block in blocks:
        btype = block.get("type", "unstyled")
        text = block.get("text", "")
        entity_ranges = block.get("entityRanges", [])
        inline_styles = block.get("inlineStyleRanges", [])

        if btype == "atomic":
            # Image or media block — look up entity by key
            if entity_ranges:
                key = str(entity_ranges[0].get("key", ""))
                entity = entity_by_key.get(key)
                if entity:
                    edata = entity.get("value", {}).get("data", entity.get("data", {}))
                    media_items = edata.get("mediaItems", [])
                    if media_items:
                        media_id = str(media_items[0].get("mediaId", ""))
                        img_url = media_id_to_url.get(media_id, "")
                        if img_url:
                            if prev_was_list:
                                lines.append("")
                                prev_was_list = False
                            lines.append(f"![image]({img_url})")
                            lines.append("")
                            continue
                    # Could be a link entity in atomic block (rare)
                    url = edata.get("url", "")
                    if url:
                        lines.append(f"[{url}]({url})")
                        lines.append("")
                        continue
            # Skip empty atomic blocks we can't resolve
            continue

        elif btype == "header-one":
            if prev_was_list:
                lines.append("")
                prev_was_list = False
            styled = _apply_block_formatting(text, inline_styles, entity_ranges, entity_by_key)
            lines.append(f"# {styled}")
            lines.append("")

        elif btype == "header-two":
            if prev_was_list:
                lines.append("")
                prev_was_list = False
            styled = _apply_block_formatting(text, inline_styles, entity_ranges, entity_by_key)
            lines.append(f"## {styled}")
            lines.append("")

        elif btype == "header-three":
            if prev_was_list:
                lines.append("")
                prev_was_list = False
            styled = _apply_block_formatting(text, inline_styles, entity_ranges, entity_by_key)
            lines.append(f"### {styled}")
            lines.append("")

        elif btype == "unordered-list-item":
            styled = _apply_block_formatting(text, inline_styles, entity_ranges, entity_by_key)
            lines.append(f"- {styled}")
            prev_was_list = True

        elif btype == "ordered-list-item":
            styled = _apply_block_formatting(text, inline_styles, entity_ranges, entity_by_key)
            lines.append(f"1. {styled}")
            prev_was_list = True

        elif btype == "blockquote":
            if prev_was_list:
                lines.append("")
                prev_was_list = False
            styled = _apply_block_formatting(text, inline_styles, entity_ranges, entity_by_key)
            lines.append(f"> {styled}")
            lines.append("")

        elif btype == "code-block":
            if prev_was_list:
                lines.append("")
                prev_was_list = False
            lines.append("```")
            lines.append(text)
            lines.append("```")
            lines.append("")

        else:
            # unstyled — regular paragraph
            if prev_was_list:
                lines.append("")
                prev_was_list = False
            if text.strip():
                styled = _apply_block_formatting(text, inline_styles, entity_ranges, entity_by_key)
                lines.append(styled)
                lines.append("")
            else:
                # Empty paragraph
                lines.append("")

    return "\n".join(lines)


# ── Markdown Formatter ─────────────────────────────────────────────────────────

def tweet_to_markdown(parsed: dict, thread: Optional[List[dict]] = None, include_article: bool = False) -> str:
    """Convert parsed tweet data to readable markdown."""
    lines = []

    author = parsed["author"]
    lines.append(f"# @{author['screen_name']} — {author['name']}")
    lines.append("")

    if parsed["created_at"]:
        lines.append(f"**Date:** {parsed['created_at']}")
    lines.append(f"**URL:** https://x.com/{author['screen_name']}/status/{parsed['id']}")

    stats = []
    if parsed["like_count"]:
        stats.append(f"❤️ {parsed['like_count']}")
    if parsed["retweet_count"]:
        stats.append(f"🔁 {parsed['retweet_count']}")
    if parsed["reply_count"]:
        stats.append(f"💬 {parsed['reply_count']}")
    if parsed["bookmark_count"]:
        stats.append(f"🔖 {parsed['bookmark_count']}")
    if stats:
        lines.append(f"**Stats:** {' · '.join(stats)}")

    if parsed["is_article"]:
        lines.append("**Type:** X Article (long-form)")

    lines.append("")
    lines.append("---")
    lines.append("")

    # Thread context (earlier tweets in the thread)
    if thread:
        for t in thread:
            t_parsed = parse_tweet(t, include_article)
            lines.append(f"> {t_parsed['text']}")
            for media in t_parsed["media"]:
                if media["type"] == "photo":
                    alt = media.get("alt_text", "image")
                    lines.append(f"> ![{alt}]({media['url']})")
            lines.append(">")
        lines.append("")
        lines.append("---")
        lines.append("")

    # Main tweet text
    lines.append(parsed["text"])
    lines.append("")

    # Media
    for media in parsed["media"]:
        if media["type"] == "photo":
            alt = media.get("alt_text", "image")
            lines.append(f"![{alt}]({media['url']})")
        elif media["type"] in ("video", "animated_gif"):
            video_url = media.get("video_url", media["url"])
            label = "GIF" if media["type"] == "animated_gif" else "Video"
            lines.append(f"[{label}]({video_url})")
        lines.append("")

    # X Article (standalone long-form content)
    if parsed.get("x_article") and include_article:
        xa = parsed["x_article"]
        lines.append("---")
        lines.append("")
        lines.append(f"## {xa['title']}")
        lines.append("")

        # Try rendering with content_state (Draft.js) for proper image placement
        rendered = _render_draftjs_article(xa)
        if rendered:
            lines.append(rendered)
        else:
            # Fallback: plain_text + images at end
            lines.append(xa["plain_text"])
            lines.append("")
            for media in xa["media"]:
                lines.append(f"![image]({media['url']})")
                lines.append("")

    # Quoted tweet
    if parsed["quoted_tweet"]:
        qt = parsed["quoted_tweet"]
        qt_author = qt["author"]
        lines.append("> **Quoted: @" + qt_author["screen_name"] + "**")
        for qt_line in qt["text"].split("\n"):
            lines.append(f"> {qt_line}")
        for media in qt["media"]:
            if media["type"] == "photo":
                alt = media.get("alt_text", "image")
                lines.append(f"> ![{alt}]({media['url']})")
        lines.append("")

    return "\n".join(lines)


# ── Media Download ─────────────────────────────────────────────────────────────

# Patterns to match media URLs in Markdown
_MD_IMAGE_RE = re.compile(r'(!\[[^\]]*\])\((\s*https?://[^)]+)\)')
_MD_LINK_RE = re.compile(r'(\[[^\]]*\])\((\s*https?://[^)]+)\)')
_HTML_MEDIA_RE = re.compile(
    r'(<(?:img|video|audio|source)\b[^>]*?\b(?:src|poster)=["\'])(https?://[^"\']+)(["\'])',
    re.IGNORECASE,
)

# Extensions considered as media
_MEDIA_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg", ".bmp", ".ico", ".avif",
    ".mp4", ".webm", ".mov", ".avi", ".mkv",
    ".mp3", ".wav", ".ogg", ".flac", ".aac", ".m4a",
}

# URL patterns that are known media hosts (download even without media extension)
_MEDIA_URL_PATTERNS = re.compile(
    r'pbs\.twimg\.com/media|pbs\.twimg\.com/tweet_video|video\.twimg\.com',
    re.IGNORECASE,
)


# Content-Type to extension mapping
_CONTENT_TYPE_EXT = {
    "image/jpeg": ".jpg", "image/png": ".png", "image/gif": ".gif",
    "image/webp": ".webp", "image/svg+xml": ".svg", "image/avif": ".avif",
    "video/mp4": ".mp4", "video/webm": ".webm", "video/quicktime": ".mov",
    "audio/mpeg": ".mp3", "audio/wav": ".wav", "audio/ogg": ".ogg",
    "audio/flac": ".flac", "audio/aac": ".aac", "audio/mp4": ".m4a",
}


def _upgrade_media_url(url: str) -> str:
    """Upgrade media URLs to original quality where possible."""
    parsed_url = urllib.parse.urlparse(url)
    if parsed_url.hostname == "pbs.twimg.com" and "/media/" in parsed_url.path:
        qs = urllib.parse.parse_qs(parsed_url.query)
        if qs.get("name", [None])[0] != "orig":
            qs["name"] = ["orig"]
            new_query = urllib.parse.urlencode(qs, doseq=True)
            return urllib.parse.urlunparse(parsed_url._replace(query=new_query))
    return url


def _ext_from_url(url: str) -> str:
    """Extract media extension from URL, checking both path and query params."""
    parsed_url = urllib.parse.urlparse(url)
    # Check path extension
    ext = Path(parsed_url.path).suffix.lower()
    ext = re.sub(r"\?.*", "", ext)
    if ext in _MEDIA_EXTENSIONS:
        return ext
    # Check ?format= query param (X/Twitter style)
    qs = urllib.parse.parse_qs(parsed_url.query)
    fmt = qs.get("format", [None])[0]
    if fmt:
        candidate = f".{fmt.lower()}"
        if candidate in _MEDIA_EXTENSIONS:
            return candidate
    return ""


def _url_to_filename(url: str, content_type: str = "") -> str:
    """Generate a deterministic filename from URL: basename-hash8.ext"""
    parsed_url = urllib.parse.urlparse(url)
    path_part = Path(parsed_url.path)

    # Try extension from URL, then content-type, then default
    ext = _ext_from_url(url)
    if not ext and content_type:
        base_ct = content_type.split(";")[0].strip().lower()
        ext = _CONTENT_TYPE_EXT.get(base_ct, "")
    if not ext:
        ext = ".jpg"  # safe default

    stem = path_part.stem or "media"
    stem = re.sub(r"[^\w\-]", "-", stem)[:60]

    url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
    return f"{stem}-{url_hash}{ext}"


def _is_media_url(url: str) -> bool:
    """Check if a URL points to media content."""
    parsed_url = urllib.parse.urlparse(url)
    ext = Path(parsed_url.path).suffix.lower()
    ext = re.sub(r"\?.*", "", ext)
    if ext in _MEDIA_EXTENSIONS:
        return True
    if _MEDIA_URL_PATTERNS.search(url):
        return True
    return False


def download_media_in_markdown(markdown: str, output_dir: str) -> str:
    """Download all media referenced in markdown, replace URLs with local paths.

    Handles:
      - Markdown images: ![alt](https://...)
      - Markdown video/media links: [Video](https://...mp4)
      - HTML media tags: <img src="...">, <video src="...">, <audio src="...">

    Returns the markdown with URLs replaced by local relative paths.
    Failed downloads keep their original URL.
    """
    os.makedirs(output_dir, exist_ok=True)
    downloaded = {}
    count = 0

    def _download(url: str) -> Optional[str]:
        nonlocal count
        url = url.strip()
        url = _upgrade_media_url(url)
        if url in downloaded:
            return downloaded[url]

        try:
            resp = requests.get(url, timeout=30, headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                              "AppleWebKit/537.36 (KHTML, like Gecko) "
                              "Chrome/131.0.0.0 Safari/537.36"
            })
            resp.raise_for_status()
            content_type = resp.headers.get("content-type", "")
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

    def _replace_md_image(m):
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

    result = _MD_IMAGE_RE.sub(_replace_md_image, markdown)
    result = _MD_LINK_RE.sub(_replace_md_link, result)
    result = _HTML_MEDIA_RE.sub(_replace_html, result)

    print(f"  Media: {count} downloaded, {sum(1 for v in downloaded.values() if v is None)} failed/skipped", file=sys.stderr)
    return result


# ── Auth Token Resolution ──────────────────────────────────────────────────────

def _resolve_auth_token() -> Optional[str]:
    """Resolve auth token with priority: env var > .env file."""
    # 1. Environment variable (highest priority)
    token = os.environ.get("X_AUTH_TOKEN")
    if token:
        return token

    # 2. .env file (~/.env or .env in current dir)
    env_paths = [
        os.path.expanduser("~/.env"),
        os.path.join(os.getcwd(), ".env"),
    ]
    for env_path in env_paths:
        if os.path.exists(env_path):
            try:
                with open(env_path) as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and line.startswith("X_AUTH_TOKEN="):
                            return line.split("=", 1)[1].strip().strip('"').strip("'")
            except OSError:
                pass

    return None


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Fetch X/Twitter post content via GraphQL API"
    )
    parser.add_argument("url", help="Tweet URL or tweet ID")
    parser.add_argument(
        "--full-article", action="store_true",
        help="Include full X Article content (long-form posts)"
    )
    parser.add_argument(
        "--json", action="store_true",
        help="Output raw parsed JSON instead of markdown"
    )
    parser.add_argument(
        "--download-media", metavar="DIR",
        help="Download all media (images/video/audio) to DIR, replace URLs with local paths"
    )
    parser.add_argument(
        "--thread", action="store_true",
        help="Include conversation thread context"
    )
    parser.add_argument(
        "--raw", action="store_true",
        help="Output raw API response JSON (for debugging)"
    )

    args = parser.parse_args()

    # ── Auth ──
    auth_token = _resolve_auth_token()
    if not auth_token:
        print("Error: X_AUTH_TOKEN is required.", file=sys.stderr)
        print("", file=sys.stderr)
        print("Option 1 — Environment variable:", file=sys.stderr)
        print("  export X_AUTH_TOKEN=your_token_here", file=sys.stderr)
        print("", file=sys.stderr)
        print("Option 2 — .env file (in ~ or current dir):", file=sys.stderr)
        print("  X_AUTH_TOKEN=your_token_here", file=sys.stderr)
        print("", file=sys.stderr)
        print("To get your auth_token:", file=sys.stderr)
        print("  1. Open x.com in browser, log in", file=sys.stderr)
        print("  2. Open DevTools → Application → Cookies → x.com", file=sys.stderr)
        print("  3. Copy the 'auth_token' cookie value", file=sys.stderr)
        sys.exit(1)

    # ── Fetch ──
    tweet_id = extract_tweet_id(args.url)
    client = XApiClient(auth_token)

    print(f"Fetching tweet {tweet_id}...", file=sys.stderr)
    raw_response = client.fetch_tweet_detail(tweet_id)

    if args.raw:
        print(json.dumps(raw_response, indent=2, ensure_ascii=False))
        return

    # ── Parse ──
    tweet_obj = find_tweet_in_response(raw_response, tweet_id)
    if not tweet_obj:
        print("Error: Tweet not found in response. It may be deleted or protected.", file=sys.stderr)
        sys.exit(1)

    parsed = parse_tweet(tweet_obj, args.full_article)

    # ── Thread ──
    thread_parsed = None
    thread_raw = None
    if args.thread:
        thread_raw = find_thread_tweets(
            raw_response, tweet_id, parsed["author"]["screen_name"]
        )
        thread_parsed = [parse_tweet(t, args.full_article) for t in thread_raw]

    # ── Output ──
    if args.json:
        output = {
            "tweet": parsed,
        }
        if thread_parsed:
            output["thread"] = thread_parsed
        print(json.dumps(output, indent=2, ensure_ascii=False))
    else:
        markdown = tweet_to_markdown(parsed, thread_raw, args.full_article)
        if args.download_media:
            markdown = download_media_in_markdown(markdown, args.download_media)
        print(markdown)


if __name__ == "__main__":
    main()
