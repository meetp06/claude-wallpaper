#!/usr/bin/env python3
"""
ClaudeCard — paste a Claude link, get the post's featured "green card" image.

This grabs the page's actual featured image (the green wrapper graphic Claude
uses for each post), NOT a screenshot. It reads the og:image / twitter:image
meta tag and downloads that file directly.

Built only for Claude pages (claude.com / claude.ai). Other domains are rejected.

Three ways to use it:

  1. Interactive (just run it, then paste a link when asked):
       python claudecard.py

  2. One link:
       python claudecard.py "https://claude.com/blog/a-harness-for-every-task-dynamic-workflows-in-claude-code"

  3. Hands-free clipboard watch:
       python claudecard.py --watch
     Copy any Claude link and the featured image downloads automatically.
     Ctrl+C to stop.

Output: one image per page, saved to your Downloads folder by default
  <slug>.<ext>          e.g. a-harness-for-every-task-...-claude-code.jpg
"""

from __future__ import annotations

import argparse
import re
import sys
import time
from pathlib import Path
from urllib.parse import urlparse, urljoin

from playwright.sync_api import sync_playwright, Error as PlaywrightError

ALLOWED_HOSTS = ("claude.com", "claude.ai")
URL_RE = re.compile(r"https?://[^\s<>\"']+", re.IGNORECASE)

# Images are saved to your Downloads folder by default. Override with -o/--out.
DEFAULT_OUT = str(Path.home() / "Downloads")

# Meta tags that hold the featured image, in priority order.
IMAGE_META = [
    "meta[property='og:image']",
    "meta[name='og:image']",
    "meta[property='twitter:image']",
    "meta[name='twitter:image']",
]


def is_claude_url(url: str) -> bool:
    host = urlparse(url).netloc.lower().split(":")[0]
    return any(host == h or host.endswith("." + h) for h in ALLOWED_HOSTS)


def normalize_url(raw: str) -> str | None:
    raw = raw.strip()
    if not raw:
        return None
    if not raw.startswith(("http://", "https://")):
        if "." not in raw or " " in raw:
            return None
        raw = "https://" + raw
    if not urlparse(raw).netloc or not is_claude_url(raw):
        return None
    return raw


def slug_from_url(url: str) -> str:
    p = urlparse(url)
    path = p.path.strip("/").replace("/", "-")
    base = path if path else p.netloc.replace("www.", "")
    base = re.sub(r"[^a-zA-Z0-9._-]", "_", base)
    return (base[:80] or "claude-card")


def ext_from(image_url: str, content_type: str | None) -> str:
    path_ext = Path(urlparse(image_url).path).suffix.lower()
    if path_ext in (".jpg", ".jpeg", ".png", ".webp", ".gif", ".svg"):
        return path_ext
    if content_type:
        m = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp",
             "image/gif": ".gif", "image/svg+xml": ".svg"}
        return m.get(content_type.split(";")[0].strip(), ".jpg")
    return ".jpg"


def find_featured_image(page, page_url: str) -> str | None:
    for sel in IMAGE_META:
        el = page.query_selector(sel)
        if el:
            content = el.get_attribute("content")
            if content:
                return urljoin(page_url, content.strip())
    return None


def download(page, image_url: str, out_dir: Path, slug: str) -> Path:
    """Download via the browser's request context (carries cookies/headers, avoids 403)."""
    out_dir.mkdir(parents=True, exist_ok=True)
    resp = page.request.get(image_url, timeout=60_000)
    if not resp.ok:
        raise PlaywrightError(f"image request returned HTTP {resp.status}")
    body = resp.body()
    ext = ext_from(image_url, resp.headers.get("content-type"))
    dest = out_dir / f"{slug}{ext}"
    dest.write_bytes(body)
    return dest


def grab(url: str, out_dir: Path, timeout_ms: int = 60_000) -> Path:
    slug = slug_from_url(url)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            page = browser.new_page()
            try:
                page.goto(url, wait_until="load", timeout=timeout_ms)
            except PlaywrightError:
                page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
            page.wait_for_timeout(800)
            image_url = find_featured_image(page, url)
            if not image_url:
                raise PlaywrightError("no featured image (og:image) found on this page")
            dest = download(page, image_url, out_dir, slug)
            print(f"  featured image: {image_url}")
            print(f"  saved: {dest.name}")
            return dest
        finally:
            browser.close()


def run_once(url: str, out_dir: Path) -> None:
    norm = normalize_url(url)
    if not norm:
        print(f"Not a Claude link (only {' / '.join(ALLOWED_HOSTS)} allowed): {url!r}",
              file=sys.stderr)
        sys.exit(1)
    print(f"Fetching {norm}")
    try:
        grab(norm, out_dir)
    except PlaywrightError as e:
        print(f"Failed: {e}", file=sys.stderr)
        sys.exit(2)
    print(f"Done -> {out_dir.resolve()}")


def run_interactive(out_dir: Path) -> None:
    """Prompt the user to paste a Claude link, then download it. Loops until quit."""
    print("Paste a Claude link and press Enter. (Press Enter on an empty line or type 'q' to quit.)")
    print(f"Images save to: {out_dir.resolve()}\n")
    while True:
        try:
            raw = input("Link> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return
        if not raw or raw.lower() in ("q", "quit", "exit"):
            return
        match = URL_RE.search(raw)
        norm = normalize_url(match.group(0) if match else raw)
        if not norm:
            print(f"  Not a Claude link (only {' / '.join(ALLOWED_HOSTS)} allowed). Try again.\n",
                  file=sys.stderr)
            continue
        print(f"Fetching {norm}")
        try:
            grab(norm, out_dir)
            print(f"Done -> {out_dir.resolve()}\n")
        except PlaywrightError as e:
            print(f"Failed: {e}\n", file=sys.stderr)


def run_watch(out_dir: Path) -> None:
    try:
        import pyperclip
    except ImportError:
        print("Watch mode needs pyperclip:  pip install pyperclip", file=sys.stderr)
        sys.exit(1)

    print(f"Watching clipboard for Claude links ({' / '.join(ALLOWED_HOSTS)}).")
    print("Copy a link and the featured image downloads automatically. Ctrl+C to stop.\n")
    last = None
    while True:
        try:
            clip = pyperclip.paste()
        except Exception:
            clip = ""
        if clip and clip != last:
            last = clip
            match = URL_RE.search(clip)
            norm = normalize_url(match.group(0) if match else clip)
            if norm:
                print(f"Detected: {norm}")
                try:
                    grab(norm, out_dir)
                    print(f"  -> {out_dir.resolve()}\n")
                except PlaywrightError as e:
                    print(f"  failed: {e}\n", file=sys.stderr)
            elif clip and (clip.startswith("http") or "." in clip):
                print(f"  (ignored, not a Claude link)")
        time.sleep(0.6)


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Download the featured green card image from a Claude page (no screenshot)."
    )
    ap.add_argument("url", nargs="?", help="A Claude link (claude.com / claude.ai).")
    ap.add_argument("--watch", action="store_true",
                    help="Auto-download whenever a Claude link is copied.")
    ap.add_argument("-o", "--out", default=DEFAULT_OUT,
                    help="Output folder (default: your Downloads folder).")
    args = ap.parse_args()

    out_dir = Path(args.out).expanduser()
    if args.watch:
        run_watch(out_dir)
    elif args.url:
        run_once(args.url, out_dir)
    else:
        run_interactive(out_dir)


if __name__ == "__main__":
    main()
