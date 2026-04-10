---
name: fengye-x-fetch
description: "Fetch X/Twitter post content including tweets, threads, and long-form articles. Converts to clean Markdown with metadata, media, and quoted tweets. Supports auth_token authentication via X's internal GraphQL API (inspired by RSSHub)."
---

# fengye-x-fetch

Fetch X/Twitter posts and convert them to clean Markdown.

## When to Use

Use this skill when the user wants to:
- Fetch or read an X/Twitter post
- Save or archive a tweet
- Get the text content of a tweet URL
- Fetch an X Article (long-form post)
- Retrieve a tweet thread

## Prerequisites

### X Auth Token

You need a valid `X_AUTH_TOKEN` to use this skill. Token is resolved in this order (first found wins):

1. **环境变量** `X_AUTH_TOKEN` — 适合本地开发
2. **`.env` 文件** `~/.env` 或当前目录 `.env` — 适合其他环境

**方式 1 — 环境变量：**
```bash
export X_AUTH_TOKEN=your_token_here
# 或写入 shell profile
echo 'export X_AUTH_TOKEN=your_token_here' >> ~/.zshrc
```

**方式 2 — .env 文件：**
```bash
echo 'X_AUTH_TOKEN=your_token_here' >> ~/.env
```

**How to get your auth_token:**
1. Open https://x.com in browser and log in
2. Open DevTools → Application → Cookies → x.com
3. Copy the `auth_token` cookie value

### Python Dependencies

```bash
pip install requests
```

## Usage

### Basic: Fetch a single tweet

```bash
export X_AUTH_TOKEN="<token>"
python <skill-path>/scripts/fetch_tweet.py "https://x.com/user/status/1234567890"
```

Output: Clean Markdown with author, date, stats, text, and media.

### Full article mode (X Articles / long posts)

```bash
python <skill-path>/scripts/fetch_tweet.py "https://x.com/user/status/1234567890" --full-article
```

### Include thread context

```bash
python <skill-path>/scripts/fetch_tweet.py "https://x.com/user/status/1234567890" --thread
```

### JSON output (for programmatic use)

```bash
python <skill-path>/scripts/fetch_tweet.py "https://x.com/user/status/1234567890" --json
```

Returns structured JSON with fields: `id`, `text`, `author`, `created_at`, `media`, `quoted_tweet`, `like_count`, etc.

### Download media

```bash
python <skill-path>/scripts/fetch_tweet.py "https://x.com/user/status/1234567890" --download-media ./assets
```

### Debug: Raw API response

```bash
python <skill-path>/scripts/fetch_tweet.py "https://x.com/user/status/1234567890" --raw
```

## Workflow for Saving a Tweet

When using this skill to save a tweet as part of a bookmark workflow:

1. **Fetch the tweet:**
   ```bash
   export X_AUTH_TOKEN=$(grep '^X_AUTH_TOKEN=' ~/.env | cut -d '=' -f 2-)
   python <skill-path>/scripts/fetch_tweet.py "<url>" --full-article --thread
   ```

2. **If you need structured data** (e.g., for metadata extraction):
   ```bash
   python <skill-path>/scripts/fetch_tweet.py "<url>" --json --full-article
   ```

3. **If you need to download images locally:**
   ```bash
   python <skill-path>/scripts/fetch_tweet.py "<url>" --download-media /path/to/assets --full-article
   ```

## Output Format

### Markdown Output

```markdown
# @username — Display Name

**Date:** Mon Jan 01 00:00:00 +0000 2026
**URL:** https://x.com/username/status/1234567890
**Stats:** ❤️ 42 · 🔁 12 · 💬 5 · 🔖 3

---

Tweet text content here...

![image](https://pbs.twimg.com/media/xxx.jpg)

> **Quoted: @other_user**
> Quoted tweet text...
```

### JSON Output

```json
{
  "tweet": {
    "id": "1234567890",
    "text": "Tweet content...",
    "author": {
      "name": "Display Name",
      "screen_name": "username",
      "avatar": "https://pbs.twimg.com/profile_images/..."
    },
    "created_at": "Mon Jan 01 00:00:00 +0000 2026",
    "media": [
      {
        "type": "photo",
        "url": "https://pbs.twimg.com/media/...",
        "alt_text": ""
      }
    ],
    "quoted_tweet": null,
    "retweet_count": 12,
    "like_count": 42,
    "reply_count": 5,
    "bookmark_count": 3,
    "is_article": false,
    "lang": "en"
  },
  "thread": []
}
```

## Troubleshooting

| Error | Cause | Fix |
|-------|-------|-----|
| `Authentication failed` | auth_token expired | Get a new token from browser cookies |
| `Rate limited` | Too many requests | Wait a few minutes |
| `Tweet not found` | Deleted/protected tweet | Nothing to do |
| `Cannot extract tweet ID` | Invalid URL format | Use format `https://x.com/user/status/ID` |

## Technical Notes

- Uses X's internal GraphQL API (same as the web client)
- Bearer token is X's public app token (embedded in their JS bundles, not a secret)
- Auth token is your session cookie — treat it as a secret
- GraphQL query IDs may rotate; update `QUERY_IDS` in the script if requests fail with 400 errors
- The script expands t.co shortened URLs to their original form
- For videos, it picks the highest bitrate MP4 variant
