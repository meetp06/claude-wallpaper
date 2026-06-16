# ClaudeCard

Paste a Claude link, get the post's featured **green card** image. Not a screenshot — the actual image Claude serves for that page.

How: it reads the page's `og:image` / `twitter:image` tag and downloads that file directly, full quality. Built only for `claude.com` / `claude.ai`; other domains are rejected.

## Setup (one time)

```bash
pip install -r requirements.txt
python -m playwright install chromium
```

## Use it

**Single link:**

```bash
python claudecard.py "https://claude.com/blog/a-harness-for-every-task-dynamic-workflows-in-claude-code"
```

**Hands-free clipboard mode:**

```bash
python claudecard.py --watch
```

Leave it running, copy any Claude link, and the featured image downloads on its own. Non-Claude links are ignored. `Ctrl+C` to stop.

## Output

One image per page in `./cards/`, named from the page slug, in its original format and resolution (the Claude blog cards are 2000×1000 JPEG):

```
a-harness-for-every-task-...-claude-code.jpg
```

## Options

| Flag | What it does |
|------|--------------|
| `-o, --out FOLDER` | Change the output folder (default `cards`). |
| `--watch` | Auto-download on clipboard Claude-link copy. |

## How it works

ClaudeCard validates the URL is on `claude.com` / `claude.ai`, loads the page with a headless Chromium (Playwright), reads the featured-image meta tag (`og:image`, then `twitter:image`), and downloads that image through the browser's request context so CDN access checks pass. No page rendering or screenshotting — you get the exact source image.

## Notes / limits

- If a page has no `og:image`, it reports that clearly instead of guessing.
- `--watch` needs `pyperclip`. On Linux it may also need `xclip` (`sudo apt install xclip`).
- The featured image is whatever the post author set; most Claude blog posts use the green wrapper card, but some posts use a different graphic.
