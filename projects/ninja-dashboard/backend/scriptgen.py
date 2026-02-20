"""Script generation wrapper — imports ninja_scriptgen directly via sys.path."""

import asyncio
import html
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Optional

# Make ~/scripts importable (env PYTHONPATH handles this in containers)
_scripts_dir = str(Path.home() / "scripts")
if _scripts_dir not in sys.path:
    sys.path.insert(0, _scripts_dir)

import ninja_scriptgen as _ns  # noqa: E402


def _fetch_article_text(url: str, timeout: int = 15) -> str:
    """Fetch a URL and extract readable text content.

    Strips HTML tags, scripts, styles, and condenses whitespace.
    Falls back to meta tags (og:title, og:description) for JS-rendered SPAs.
    Returns up to ~3000 chars of article body text.
    """
    req = urllib.request.Request(url, headers={
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/131.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,*/*",
        "Accept-Language": "en-US,en;q=0.9",
    })

    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read()
        charset = resp.headers.get_content_charset() or "utf-8"
        page_html = raw.decode(charset, errors="replace")

    # 1. Extract meta tags first (always useful, works for SPAs)
    meta_parts = []
    for attr in ("og:title", "og:description", "twitter:title", "twitter:description",
                 "description"):
        # Match both property= and name= patterns
        m = re.search(
            rf'<meta[^>]*(?:property|name)=["\']?{re.escape(attr)}["\']?[^>]*content=["\']([^"\']+)["\']',
            page_html, re.IGNORECASE,
        )
        if not m:
            # Try reversed order (content before property)
            m = re.search(
                rf'<meta[^>]*content=["\']([^"\']+)["\']?[^>]*(?:property|name)=["\']?{re.escape(attr)}["\']',
                page_html, re.IGNORECASE,
            )
        if m:
            meta_parts.append(html.unescape(m.group(1).strip()))

    title_m = re.search(r"<title[^>]*>(.*?)</title>", page_html, re.DOTALL | re.IGNORECASE)
    if title_m:
        title_text = html.unescape(title_m.group(1).strip())
        if title_text and title_text not in meta_parts:
            meta_parts.insert(0, title_text)

    meta_text = ". ".join(dict.fromkeys(meta_parts))  # dedupe while preserving order

    # 2. Try extracting body text
    body_html = page_html
    for tag in ("script", "style", "nav", "header", "footer", "aside", "noscript", "svg"):
        body_html = re.sub(
            rf"<{tag}[\s>].*?</{tag}>", " ", body_html, flags=re.DOTALL | re.IGNORECASE
        )

    # Try to find main content area
    main_match = re.search(
        r'<(?:article|main|div[^>]*class="[^"]*(?:content|article|post|entry|body)[^"]*")[^>]*>(.*?)</(?:article|main|div)>',
        body_html, re.DOTALL | re.IGNORECASE,
    )
    content = main_match.group(1) if main_match else body_html

    # Strip HTML tags
    body_text = re.sub(r"<[^>]+>", " ", content)
    body_text = html.unescape(body_text)
    body_text = re.sub(r"\s+", " ", body_text).strip()

    # 3. Pick best result: body text if substantial, otherwise meta tags
    if len(body_text) > 200:
        text = body_text
    elif meta_text:
        text = meta_text
    else:
        text = body_text  # whatever we got

    # Trim to ~3000 chars
    if len(text) > 3000:
        text = text[:3000].rsplit(" ", 1)[0] + "..."

    return text


def _context_from_url(url: str) -> str:
    """Extract meaningful context from URL path segments as a last resort.

    e.g. 'https://page.onstove.com/chaoszeronightmare/en/view/12171622'
    → 'chaos zero nightmare (from page.onstove.com)'
    """
    from urllib.parse import urlparse

    parsed = urlparse(url)
    host = parsed.hostname or ""
    noise = {"en", "view", "post", "article", "articles", "news", "blog", "p", "s", "t", "page", "pages", "category", "tag", "comments"}
    path_parts = [p for p in parsed.path.split("/") if p and not p.isdigit() and p.lower() not in noise]

    if not path_parts:
        return ""

    # Convert slugs to readable text
    readable = []
    for part in path_parts:
        # Split camelCase
        words = re.sub(r"([a-z])([A-Z])", r"\1 \2", part)
        # Split on hyphens, underscores
        words = re.sub(r"[-_]+", " ", words)
        readable.append(words.strip())

    context = ", ".join(readable)
    return f"{context} (from {host}). Look up this topic and write a script about it."


async def generate_script(
    url: Optional[str] = None,
    text: Optional[str] = None,
    target_length_sec: int = 60,
) -> str:
    """
    Generate a YouTube Shorts script from an article URL or raw text.
    target_length_sec controls the word budget (mapped to MAX_WORDS).
    Returns the full script text (intro + body + outro).
    """
    if not url and not text:
        raise ValueError("Provide url or text")

    # If URL provided, fetch article content first
    article_text = None
    if url:
        try:
            article_text = await asyncio.to_thread(_fetch_article_text, url)
            if article_text and len(article_text.strip()) > 50:
                print(f"[scriptgen] Fetched {len(article_text)} chars from {url}")
            else:
                article_text = None
                print(f"[scriptgen] URL returned too little text, trying Google cache...")
        except Exception as e:
            print(f"[scriptgen] Could not fetch URL ({e}), trying Google cache...")
            article_text = None

        # Fallback: try Google's webcache
        if not article_text:
            try:
                cache_url = f"https://webcache.googleusercontent.com/search?q=cache:{url}"
                article_text = await asyncio.to_thread(_fetch_article_text, cache_url)
                if article_text and len(article_text.strip()) > 50:
                    print(f"[scriptgen] Got {len(article_text)} chars from Google cache")
                else:
                    article_text = None
            except Exception:
                article_text = None

        # Last resort: extract context from URL path segments
        if not article_text:
            article_text = _context_from_url(url)
            if article_text:
                print(f"[scriptgen] Extracted context from URL: {article_text[:80]}")

    def _sync_generate() -> str:
        # Temporarily patch module globals for this call
        orig_target = _ns.TARGET_DURATION_SEC
        orig_max_words = _ns.MAX_WORDS

        _ns.TARGET_DURATION_SEC = target_length_sec
        _ns.MAX_WORDS = int(target_length_sec / 60 * _ns.WORDS_PER_MINUTE)

        try:
            if url:
                # Use fetched article text if available, otherwise just the URL
                summary = article_text or f"Article URL: {url}"
                # Try to extract a title from the fetched text
                title = url
                if article_text:
                    # First sentence or first 100 chars make a decent title
                    first_line = article_text.split(".")[0].strip()
                    if 10 < len(first_line) < 120:
                        title = first_line

                story = _ns.Story(
                    title=title,
                    summary=summary,
                    url=url,
                    source="Custom URL",
                    category="tech",
                )
            else:
                # Use first line as title, first 500 chars as summary
                title = (text or "").split("\n")[0][:100].strip() or "Custom Article"
                summary = (text or "")[:500]
                story = _ns.Story(
                    title=title,
                    summary=summary,
                    url="",
                    source="Custom Text",
                    category="tech",
                )
            script = _ns.generate_script_with_llm(story)
            return script.full_text
        finally:
            # Always restore originals
            _ns.TARGET_DURATION_SEC = orig_target
            _ns.MAX_WORDS = orig_max_words

    return await asyncio.to_thread(_sync_generate)
