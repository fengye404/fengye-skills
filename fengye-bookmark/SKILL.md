---
name: fengye-bookmark
description: "Save and archive web articles, blog posts, X/Twitter threads, and other online content to a local bookmark collection. Handles content fetching, media downloading, metadata extraction, and index management. Use when the user wants to save, bookmark, archive, or collect any URL for later reference."
---

# fengye-bookmark

Save web content (articles, X posts, blog posts, etc.) to a structured local bookmark collection with automatic content fetching, media downloading, and index management.

## When to Use

Use this skill when the user wants to:
- Save or bookmark a web article or blog post
- Archive an X/Twitter thread or post
- Collect content from any URL for later reference
- Store online content locally with all assets

## Storage Layout

```
~/workspace/blog/bookmarks/
├── index.csv          # Title, Category, URL, Description, Saved Path
├── articles/          # Markdown files
│   ├── how-to-build-apis.md
│   └── understanding-react-hooks.md
└── assets/            # Downloaded media, organized per article
    ├── how-to-build-apis/
    │   ├── arch-diagram-a3f2b1c9.png
    │   └── demo-video-7d4e5f6a.mp4
    └── understanding-react-hooks/
        └── hooks-lifecycle-8e2b3a1f.png
```

Each article's media is stored in `assets/<article-name>/` where `<article-name>` matches the markdown filename (without `.md`).

**Absolute path:** `/Users/fengye/workspace/blog/bookmarks/`

## Complete Workflow

### Step 1: Check for Duplicates

Read `/Users/fengye/workspace/blog/bookmarks/index.csv` and check if the URL already exists.

If duplicate found:
- Ask the user: "This URL is already bookmarked as '[title]'. Update it?"
- If yes, proceed with the same filename from the index
- If no, abort

### Step 2: Generate Filename

Before fetching, decide the filename based on the URL and page title. You can infer a reasonable name from the URL path, or do a quick lightweight fetch (without `--download-media`) to get the title first.

Rules:
- At least 3 English words separated by hyphens
- Based on the article title or URL
- Lowercase, no special characters
- Ensure uniqueness (check existing files in `articles/`)
- The name (without `.md`) will also be the asset subdirectory name

Examples:
- "How to Build Better APIs" → `how-to-build-better-apis`
- "Understanding React Hooks" → `understanding-react-hooks`
- "AI 安全研究进展" → `ai-safety-research-progress`

Create the asset directory:
```bash
mkdir -p /Users/fengye/workspace/blog/bookmarks/assets/<article-name>
```

### Step 3: Fetch Content (Dual Fetch)

Fetch the same URL with **both** fetchers, then compare and pick the more complete result.

#### 3a. Primary fetcher (by URL type)

| URL Pattern | Tool | Command |
|---|---|---|
| `x.com/*` or `twitter.com/*` | fengye-x-fetch | `python <skill-path>/scripts/fetch_tweet.py "<url>" --full-article --download-media /Users/fengye/workspace/blog/bookmarks/assets/<article-name>` |
| Everything else | fengye-markdown-fetch | `python <skill-path>/scripts/fetch_markdown.py "<url>" --download-media /Users/fengye/workspace/blog/bookmarks/assets/<article-name>` |

#### 3b. Secondary fetcher (always run)

Regardless of URL type, also fetch with fengye-markdown-fetch:

```bash
python <fengye-markdown-fetch-skill-path>/scripts/fetch_markdown.py "<url>" --download-media /Users/fengye/workspace/blog/bookmarks/assets/<article-name>
```

> For non-X/Twitter URLs, 3a and 3b use the same tool — no need to run twice.

#### 3c. Compare and choose

With both results in hand:
1. Compare body length, whether a title is present, and image count
2. Check for truncation (abnormally short body, incomplete ending)
3. **Pick the more complete version** as the final content
4. If the two differ significantly, ask the user which to keep

**Important:** If the X_AUTH_TOKEN is needed and not set, load it from the environment (`~/.zshrc`) or `~/.env`.

### Step 4: Fix Asset Paths

The `--download-media` flag already downloads media and replaces URLs. But the paths in the output will be absolute (`/Users/fengye/workspace/blog/bookmarks/assets/<article-name>/xxx.png`).

**Replace them with relative paths** for portability:
- `/Users/fengye/workspace/blog/bookmarks/assets/<article-name>/xxx.png` → `../assets/<article-name>/xxx.png`

This ensures the markdown renders correctly from the `articles/` directory.

### Step 5: Extract Metadata

From the fetched content, extract or infer:

- **Title**: From the article's `<h1>`, frontmatter `title:`, or first `# heading`
- **Category**: Infer from content. Common categories:
  - Technology, Programming, AI/ML, Design, Business, Science, Personal Development, etc.
  - If uncertain, ask the user
- **Description**: 1-2 sentence summary of the article's main point

### Step 6: Save Markdown File

Save to `/Users/fengye/workspace/blog/bookmarks/articles/<article-name>.md`:

```markdown
---
title: [Article Title]
url: [Original URL]
category: [Category]
saved_date: [YYYY-MM-DD]
---

# [Article Title]

**Original URL:** [URL]
**Category:** [Category]
**Saved:** [YYYY-MM-DD]

---

[Article content with relative asset paths]
```

### Step 7: Update Index

Append a new row to `/Users/fengye/workspace/blog/bookmarks/index.csv`:

```
[title],[category],[url],[desc],[saved-path]
```

### Step 8: Sync to Blog Bookmarks Page

After saving the bookmark locally, add it to the blog's bookmarks page.

**Data file:** `/Users/fengye/workspace/blog/fengye404.github.io/source/_data/bookmarks.yml`

Append a new entry under the appropriate `class_name` group (match by category):

```yaml
    - title: "[Article Title]"
      link: [Original URL]
      description: [1-2 sentence description]
      date: "[YYYY-MM-DD]"
```

Rules:
- Find an existing group whose `class_name` matches the article's category
- If no matching group exists, create a new one at the end of the file
- **Date must be quoted** (`"2026-04-11"`) to avoid YAML parsing it as a Date object
- Title should also be quoted if it contains special characters

After updating the YAML file, rebuild and deploy the blog:

```bash
cd /Users/fengye/workspace/blog/fengye404.github.io
npx hexo clean && npx hexo generate && npx hexo deploy
git add -A && git commit -m "bookmark: add [article-name]" && git push origin hexo-source
```

Rules:
- Quote fields that contain commas
- `saved-path` is relative: `articles/[filename].md`
- If index.csv doesn't exist, create it with a header row first:
  ```
  title,category,url,desc,saved_path
  ```

## Error Handling

- Content fetch fails → inform user, suggest trying the other fetcher
- Media download fails → keep original URL (the `--download-media` flag already handles this)
- Category uncertain → ask the user
- Duplicate filename → append `-2`, `-3`, etc.

## Success Message

```
✓ Bookmarked: [Title]
  Category: [Category]
  Saved to: saved/[filename].md
  Assets: [count] media files downloaded
```
