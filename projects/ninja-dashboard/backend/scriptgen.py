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


_GAMING_KEYWORDS = {
    "gacha", "banner", "update", "patch", "character", "rework", "nerf", "buff",
    "meta", "tier list", "gameplay", "trailer", "ps5", "ps4", "xbox", "nintendo",
    "switch", "steam", "playstation", "game pass", "genshin", "honkai", "wuthering",
    "zelda", "mario", "pokemon", "fortnite", "valorant", "apex", "league", "elden ring",
    "final fantasy", "souls", "remake", "remaster", "dlc", "expansion", "raid",
    "pvp", "pve", "mmo", "rpg", "fps", "battle pass", "season pass", "launch",
    "reveal", "state of play", "direct", "showcase", "game awards", "e3", "tgs",
    "pity", "apologems", "copium", "summon", "pull", "roll", "reroll",
}


def _detect_content_category(title: str, summary: str) -> str:
    """Auto-detect content category from title and summary text.

    Returns 'gaming' if gaming keywords are found, otherwise 'tech'.
    """
    combined = f"{title} {summary}".lower()
    matches = sum(1 for kw in _GAMING_KEYWORDS if kw in combined)
    return "gaming" if matches >= 2 else "tech"


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

                category = _detect_content_category(title, summary)
                story = _ns.Story(
                    title=title,
                    summary=summary,
                    url=url,
                    source="Custom URL",
                    category=category,
                )
            else:
                # Use first line as title, first 500 chars as summary
                title = (text or "").split("\n")[0][:100].strip() or "Custom Article"
                summary = (text or "")[:500]
                category = _detect_content_category(title, summary)
                story = _ns.Story(
                    title=title,
                    summary=summary,
                    url="",
                    source="Custom Text",
                    category=category,
                )
            script = _ns.generate_script_with_llm(story)
            return script.full_text
        finally:
            # Always restore originals
            _ns.TARGET_DURATION_SEC = orig_target
            _ns.MAX_WORDS = orig_max_words

    return await asyncio.to_thread(_sync_generate)


# ---------------------------------------------------------------------------
# Dual-Anchor Script Generation (Ninja News Network)
# ---------------------------------------------------------------------------

DUAL_ANCHOR_INTRO = (
    "NINJA: What's up my fellow Ninjas! This is Neurodivergent Ninja here "
    "and welcome to the Ninja News Network!"
)

DUAL_ANCHOR_OUTRO = (
    "NINJA: That's all for this one! Thanks for watching, hit that like and "
    "subscribe — it really helps the channel grow.\n"
    "GLITCH: Stay glitchy.\n"
    "NINJA: Peace out ninjas, see you next time!"
)


async def generate_dual_anchor_script(
    url: Optional[str] = None,
    text: Optional[str] = None,
    target_length_sec: int = 90,
) -> str:
    """Generate a dual-anchor dialogue script with NINJA: and GLITCH: labels.

    Returns a full script including intro and outro.
    """
    if not url and not text:
        raise ValueError("Provide url or text")

    # Fetch article content (reuse same logic)
    story_context = text or ""
    if url:
        try:
            fetched = await asyncio.to_thread(_fetch_article_text, url)
            if fetched and len(fetched.strip()) > 50:
                story_context = fetched
            else:
                story_context = _context_from_url(url) or f"Article URL: {url}"
        except Exception:
            story_context = _context_from_url(url) or f"Article URL: {url}"

    # Word budget: ~130 wpm speech, minus intro/outro (~40 words)
    body_max_words = max(30, int(target_length_sec / 60 * 130) - 40)

    llm_prompt = f"""You are writing a script for "Ninja News Network", a dual-anchor gaming news show.

TWO CHARACTERS:
- NINJA: The optimistic hype man. Gets excited about announcements. Uses slang like "yo", "dude", "let's go". Always sees the positive side. Catchphrase when excited: "That's a CRITICAL HIT!"
- GLITCH: The analytical skeptic co-host. Questions hype, looks for the catch. Sarcastic humor, references data and history. Balances Ninja's enthusiasm. Says things like "Patch notes or it didn't happen" and "That's copium and you know it."

FORMAT RULES:
- Every line starts with "NINJA:" or "GLITCH:"
- Lines alternate naturally (like a real conversation, not rigid turn-taking)
- 6-12 exchanges total
- Each line is 1-3 sentences max
- Do NOT include any intro or outro (those are added automatically)
- Start with NINJA reacting to the news, GLITCH responds
- End on a fun note — either agreement, playful disagreement, or a callback joke
- The dialogue should feel like two friends who genuinely enjoy each other's company

ENERGY:
- This is a YouTube Short, so keep the energy HIGH from the first word
- No slow buildups — jump straight into the most exciting part of the news
- Use emotional hooks: excitement, surprise, skepticism, humor
- Make viewers want to comment which host they agree with

STORY TO COVER:
{story_context[:2500]}

TARGET: ~{body_max_words} words for the dialogue body.
Return ONLY the dialogue lines (NINJA: and GLITCH: labels), nothing else. No stage directions, no brackets, no narration."""

    def _sync_generate() -> str:
        import anthropic

        api_key = _ns.get_api_key("anthropic")
        if not api_key:
            raise RuntimeError("Anthropic API key not found")

        client = anthropic.Anthropic(api_key=api_key)
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            messages=[{"role": "user", "content": llm_prompt}],
        )

        body = message.content[0].text.strip()

        # Validate: ensure it has NINJA: and GLITCH: labels
        if "NINJA:" not in body or "GLITCH:" not in body:
            print(f"[scriptgen] WARNING: LLM output missing speaker labels, using as-is")

        # Assemble full script: intro + body + outro
        full_script = f"{DUAL_ANCHOR_INTRO}\n{body}\n{DUAL_ANCHOR_OUTRO}"
        return full_script

    return await asyncio.to_thread(_sync_generate)
