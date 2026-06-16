# ClaudeCard

Paste a Claude link, get the post's featured **green card** image. Not a screenshot — the actual image Claude serves for that page.

How: it reads the page's `og:image` / `twitter:image` tag and downloads that file directly, full quality. Built only for `claude.com` / `claude.ai`; other domains are rejected.

## Install (one command)

Open the **Terminal** app on your Mac and paste this:

```bash
curl -fsSL https://raw.githubusercontent.com/meetp06/claude-wallpaper/main/install.sh | bash
```

That's it. The installer does everything for you — no manual steps:

- finds Python 3 on your machine (works with `python3`, `python3.11`, `python3.12`, … any 3.8+), and **installs it automatically** (via Homebrew) if you don't have it
- creates an isolated virtual environment so nothing touches your system Python
- installs all dependencies + headless Chromium
- adds a `claudecard` command you can run from anywhere

Linux is supported too (Python is installed via `apt` if missing).

## Use it

After installing, just run:

```bash
claudecard
```

It asks you to **paste a Claude link**. Paste one, press Enter, and the featured image is **saved straight to your Downloads folder**. Paste as many as you like; press Enter on an empty line (or type `q`) to quit.

Prefer one-shot or hands-free? Both still work:

```bash
claudecard "https://claude.com/blog/a-harness-for-every-task-dynamic-workflows-in-claude-code"   # single link
claudecard --watch                                                                                # auto-grab whenever you copy a Claude link
```

`--watch` leaves it running — copy any Claude link and the image downloads on its own. Non-Claude links are ignored. `Ctrl+C` to stop.

> Running from source instead of the installer? Use `python3 claudecard.py …` (set up deps once with `pip install -r requirements.txt && python3 -m playwright install chromium`).

## Output

One image per page, saved to your **Downloads** folder, named from the page slug, in its original format and resolution (the Claude blog cards are 2000×1000 JPEG):

```
~/Downloads/a-harness-for-every-task-...-claude-code.jpg
```

Want them somewhere else? Add `-o /some/folder`.

## Options

| Flag | What it does |
|------|--------------|
| `-o, --out FOLDER` | Change the output folder (default: your `~/Downloads` folder). |
| `--watch` | Auto-download on clipboard Claude-link copy. |

## How it works

ClaudeCard validates the URL is on `claude.com` / `claude.ai`, loads the page with a headless Chromium (Playwright), reads the featured-image meta tag (`og:image`, then `twitter:image`), and downloads that image through the browser's request context so CDN access checks pass. No page rendering or screenshotting — you get the exact source image.

## Notes / limits

- If a page has no `og:image`, it reports that clearly instead of guessing.
- `--watch` needs `pyperclip`. On Linux it may also need `xclip` (`sudo apt install xclip`).
- The featured image is whatever the post author set; most Claude blog posts use the green wrapper card, but some posts use a different graphic.
