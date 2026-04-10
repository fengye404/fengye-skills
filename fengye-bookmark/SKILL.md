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
~/Documents/bookmarks/
├── index.csv          # Title, Category, URL, Description, Saved Path
├── saved/             # Markdown files
│   ├── how-to-build-apis.md
│   └── understanding-react-hooks.md
└── assets/            # Downloaded media (images, video, audio)
    ├── arch-diagram-a3f2b1c9.png
    └── demo-video-7d4e5f6a.mp4
```

**Absolute path:** `/Users/fengye/Documents/bookmarks/`

## Complete Workflow

### Step 1: Fetch Content (双重获取)

**同时使用两个 fetcher 抓取同一 URL**，对比后选择更完整的版本。

#### 1a. 专用 fetcher（按 URL 类型选）

| URL Pattern | Tool | Command |
|---|---|---|
| `x.com/*` or `twitter.com/*` | fengye-x-fetch | `python <skill-path>/scripts/fetch_tweet.py "<url>" --full-article --download-media /Users/fengye/Documents/bookmarks/assets` |
| Everything else | fengye-markdown-fetch | `python <skill-path>/scripts/fetch_markdown.py "<url>" --download-media /Users/fengye/Documents/bookmarks/assets` |

#### 1b. 通用 fetcher（始终执行）

无论 URL 类型，都额外用 fengye-markdown-fetch 再抓一次：

```bash
python <fengye-markdown-fetch-skill-path>/scripts/fetch_markdown.py "<url>" --download-media /Users/fengye/Documents/bookmarks/assets
```

> 对于非 X/Twitter URL，1a 和 1b 使用的是同一个工具，无需重复执行。

#### 1c. 对比选择

拿到两份结果后：
1. 比较正文长度、标题是否存在、图片数量
2. 检查是否有内容截断（正文异常短、末尾不完整）
3. **选择更完整的版本**作为最终内容
4. 如果两者差异较大，询问用户偏好

**Important:** If the X_AUTH_TOKEN is needed and not set, it should be loaded from the environment (`~/.zshrc`) or `~/.env`.

### Step 2: Check for Duplicates

Before saving, read `/Users/fengye/Documents/bookmarks/index.csv` and check if the URL already exists.

If duplicate found:
- Ask the user: "This URL is already bookmarked as '[title]'. Update it?"
- If yes, proceed with the same filename from the index
- If no, abort

### Step 3: Generate Filename

Rules:
- At least 3 English words separated by hyphens
- Based on the article title
- Lowercase, no special characters
- Ensure uniqueness (check existing files in `saved/`)
- Add `.md` extension

Examples:
- "How to Build Better APIs" → `how-to-build-better-apis.md`
- "Understanding React Hooks" → `understanding-react-hooks.md`
- "AI 安全研究进展" → `ai-safety-research-progress.md`

### Step 4: Fix Asset Paths

The `--download-media` flag already downloads media and replaces URLs. But the paths in the output will be absolute (`/Users/fengye/Documents/bookmarks/assets/xxx.png`).

**Replace them with relative paths** for portability:
- `/Users/fengye/Documents/bookmarks/assets/xxx.png` → `../assets/xxx.png`

This ensures the markdown renders correctly from the `saved/` directory.

### Step 5: Extract Metadata

From the fetched content, extract or infer:

- **Title**: From the article's `<h1>`, frontmatter `title:`, or first `# heading`
- **Category**: Infer from content. Common categories:
  - Technology, Programming, AI/ML, Design, Business, Science, Personal Development, etc.
  - If uncertain, ask the user
- **Description**: 1-2 sentence summary of the article's main point

### Step 6: Save Markdown File

Save to `/Users/fengye/Documents/bookmarks/saved/[filename].md`:

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

Append a new row to `/Users/fengye/Documents/bookmarks/index.csv`:

```
[title],[category],[url],[desc],[saved-path]
```

Rules:
- Quote fields that contain commas
- `saved-path` is relative: `saved/[filename].md`
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
