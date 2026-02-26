#!/usr/bin/env python3
"""
ninja_scriptgen.py — Ninja content script generator

Fetches trending tech/gaming news and generates short-form video scripts
optimized for YouTube Shorts and Instagram Reels.

Usage:
    # Fetch trending topics and show options
    python ninja_scriptgen.py --discover

    # Generate a script from a topic
    python ninja_scriptgen.py --topic "NVIDIA just dropped a new GPU"

    # Auto-generate from today's top story
    python ninja_scriptgen.py --auto

    # Generate and pipe directly into the video pipeline
    python ninja_scriptgen.py --auto --pipeline

    # Custom category
    python ninja_scriptgen.py --discover --category gaming
"""

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
import time
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Dict


# =============================================================================
# Configuration
# =============================================================================

BRAND_NAME = "Neurodivergent Ninja"
TARGET_DURATION_SEC = 50  # Target spoken duration (40-60s with intro/outro)
WORDS_PER_MINUTE = 155    # Average speaking rate for casual delivery
MAX_WORDS = int(TARGET_DURATION_SEC / 60 * WORDS_PER_MINUTE)  # ~129 words

# Brand ID — short tag placed AFTER the hook, not before it
SHORT_BRAND_ID = "Hi, I'm Neurodivergent Ninja."

# Legacy intro kept for reference / dual-anchor use
STANDARD_INTRO = "What's up my fellow Ninjas, this is Neurodivergent Ninja here back with another video."

# Outro — ninja-flavored sign-off (CTA is in the script body now)
STANDARD_OUTRO = "Stay sharp, stay dangerous. Catch you on the next one."

# RSS Feeds by category
RSS_FEEDS = {
    "tech": [
        ("The Verge", "https://www.theverge.com/rss/index.xml"),
        ("Ars Technica", "https://feeds.arstechnica.com/arstechnica/index"),
        ("TechCrunch", "https://techcrunch.com/feed/"),
        ("Hacker News (Top)", "https://hnrss.org/frontpage?count=10"),
    ],
    "gaming": [
        ("IGN", "https://feeds.feedburner.com/ign/all"),
        ("GameSpot", "https://www.gamespot.com/feeds/mashup/"),
        ("Kotaku", "https://kotaku.com/rss"),
        ("PC Gamer", "https://www.pcgamer.com/rss/"),
    ],
    "ai": [
        ("AI News (The Verge)", "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml"),
        ("Hacker News (Top)", "https://hnrss.org/frontpage?count=10"),
    ],
}

# Script templates per content type
SCRIPT_TEMPLATES = {
    "tech_news": {
        "name": "Tech News Drop",
        "structure": "hook → brand tag → what happened → why it matters → ninja's take → community question",
        "tone": "Informative but energetic. Like a friend pulling you aside to tell you something wild.",
    },
    "gaming": {
        "name": "Gaming Hot Take",
        "structure": "hook → brand tag → MAIN topic (fact/stakes/reaction) → transition → side items (quick hits) → micro-summary → ninja's take on MAIN → community question",
        "tone": "Passionate gamer energy. Use gacha vocabulary naturally (kit, pity, apologems, copium). You have strong opinions.",
    },
    "ai": {
        "name": "AI Update",
        "structure": "hook → brand tag → what's new → real-world impact → ninja's take → community question",
        "tone": "Excited but grounded. Make AI accessible, not scary. You're the friend who makes tech make sense.",
    },
}


@dataclass
class Story:
    """A news story from an RSS feed."""
    title: str
    summary: str
    url: str
    source: str
    published: Optional[str] = None
    category: str = "tech"

    def __str__(self):
        return f"[{self.source}] {self.title}"


@dataclass
class Script:
    """A generated video script."""
    title: str
    hook: str
    body: str
    full_text: str
    word_count: int
    estimated_duration_sec: float
    source_story: Optional[Story] = None
    category: str = "tech"
    template: str = "tech_news"


# =============================================================================
# RSS Feed Fetching
# =============================================================================

def fetch_rss(url: str, timeout: int = 15) -> str:
    """Fetch RSS feed content."""
    req = urllib.request.Request(url, headers={
        "User-Agent": "NinjaScriptGen/1.0 (Content Pipeline)",
    })
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", errors="replace")


def parse_rss(xml_content: str, source: str, category: str) -> List[Story]:
    """Parse RSS/Atom feed into Story objects."""
    stories = []
    try:
        root = ET.fromstring(xml_content)
    except ET.ParseError:
        return stories

    # Handle both RSS and Atom formats
    namespaces = {
        "atom": "http://www.w3.org/2005/Atom",
        "dc": "http://purl.org/dc/elements/1.1/",
        "content": "http://purl.org/rss/1.0/modules/content/",
    }

    # Try RSS format first
    items = root.findall(".//item")
    if items:
        for item in items[:5]:  # Top 5 per feed
            title = item.findtext("title", "").strip()
            summary = item.findtext("description", "").strip()
            url = item.findtext("link", "").strip()
            published = item.findtext("pubDate", "")

            # Strip HTML from summary
            summary = re.sub(r"<[^>]+>", "", summary)
            summary = summary[:500]  # Truncate

            if title:
                stories.append(Story(
                    title=title,
                    summary=summary,
                    url=url,
                    source=source,
                    published=published,
                    category=category,
                ))

    # Try Atom format
    if not items:
        entries = root.findall(".//atom:entry", namespaces) or root.findall(".//entry")
        for entry in entries[:5]:
            title = (entry.findtext("atom:title", "", namespaces)
                     or entry.findtext("title", "")).strip()
            summary = (entry.findtext("atom:summary", "", namespaces)
                       or entry.findtext("summary", "")).strip()

            # Get link
            link_elem = entry.find("atom:link", namespaces) or entry.find("link")
            url = ""
            if link_elem is not None:
                url = link_elem.get("href", "")

            published = (entry.findtext("atom:published", "", namespaces)
                         or entry.findtext("published", ""))

            summary = re.sub(r"<[^>]+>", "", summary)[:500]

            if title:
                stories.append(Story(
                    title=title,
                    summary=summary,
                    url=url,
                    source=source,
                    published=published,
                    category=category,
                ))

    return stories


def discover_stories(categories: List[str] = None) -> List[Story]:
    """Fetch stories from all configured RSS feeds."""
    if categories is None:
        categories = ["tech", "gaming"]

    all_stories = []
    for category in categories:
        feeds = RSS_FEEDS.get(category, [])
        for source_name, feed_url in feeds:
            try:
                xml_content = fetch_rss(feed_url)
                stories = parse_rss(xml_content, source_name, category)
                all_stories.extend(stories)
            except Exception as e:
                print(f"  ⚠️  Failed to fetch {source_name}: {e}", file=sys.stderr)

    return all_stories


# =============================================================================
# Script Generation (LLM-powered)
# =============================================================================

def get_api_key(provider: str) -> Optional[str]:
    """Get API key for a provider."""
    env_var = f"{provider.upper()}_API_KEY"
    key = os.environ.get(env_var)
    if key:
        return key

    # Try known env files
    env_files = [
        "/home/ndninja/projects/llm-council/.env",
        "/home/ndninja/projects/content-automation/.env",
        "/home/ndninja/n8n/.env",
    ]
    for env_file in env_files:
        if os.path.exists(env_file):
            with open(env_file) as f:
                for line in f:
                    if line.startswith(f"{env_var}="):
                        return line.strip().split("=", 1)[1].strip('"').strip("'")
    return None


def generate_script_with_llm(story: Story, template_key: str = None) -> Script:
    """Generate a video script using an LLM."""

    # Auto-detect template from category
    if template_key is None:
        template_key = {
            "tech": "tech_news",
            "gaming": "gaming",
            "ai": "ai",
        }.get(story.category, "tech_news")

    template = SCRIPT_TEMPLATES[template_key]

    # Calculate body word budget (total minus brand ID + outro)
    brand_words = len(SHORT_BRAND_ID.split())
    outro_words = len(STANDARD_OUTRO.split())
    body_max_words = MAX_WORDS - brand_words - outro_words

    prompt = f"""You are a script writer for "{BRAND_NAME}", a YouTube Shorts channel covering gaming and tech news.
Write a short-form video script based on this story.

STORY:
Title: {story.title}
Summary: {story.summary}
Source: {story.source}

SCRIPT STRUCTURE (follow this exact order):

1. HOOK (1-2 sentences, ~12 words): The single most interesting or shocking fact from this story. NO greeting. NO name. Jump straight into the news. Stop the scroll.
   Good examples: "Sony just ended cross-gen support and nobody's talking about it."
   "This new banner costs 400 bucks to guarantee — and players are DEFENDING it."
   Bad examples: "Hey guys, today we're talking about..." or "Big news dropped today..."

2. BRAND TAG (fixed — do NOT change this): "{SHORT_BRAND_ID}"

3. MAIN TOPIC (~40-50 words): The single biggest story. Give it the full Fact → Stakes/Implication → Reaction arc. Go DEEP on this one — explain WHY it matters, not just WHAT happened. Every sentence should make the viewer need the next one.

4. TRANSITION + SIDE ITEMS (~15-20 words total): Use a verbal signpost to shift gears, then give 1-2 quick mentions of related news. One sentence each, max.
   Transition phrases (pick one): "But here's the real headline —" / "Oh and real quick —" / "Now the part everyone's sleeping on —" / "Quick side note though —"

5. MICRO-SUMMARY (1 short sentence): Re-anchor the viewer on the main story before your take. Example: "So yeah, this banner is basically a whale trap."

6. NINJA'S TAKE (exactly 1 sentence starting with "Here's what I actually think —"): A specific, opinionated stance on the MAIN TOPIC. NOT vague ("this is big news"). BE SPECIFIC ("Sony knows 30 percent of players still buy physical and this kills the used games market"). Take a real position.

7. COMMUNITY HOOK (1 sentence): A specific question that drives comments. Tie it to the main topic. "Are you pulling on this banner or saving?" NOT "What do you think? Let me know below."

RULES:
- Format: {template['name']}
- Tone: {template['tone']}
- Target length: {body_max_words} words TOTAL (hook through community hook — the outro is added automatically)
- ONE main course, TWO side dishes — most of the word budget goes to the MAIN TOPIC
- Use short, punchy sentences. No filler words.
- Write as one continuous flowing paragraph — NO paragraph breaks (they cause TTS pauses)
- Write ONLY spoken script text — no stage directions, no [brackets], no formatting
- Do NOT include any greeting, sign-off, or the outro — those are added automatically
- The entire script should flow naturally as energetic casual speech

OUTPUT: Return ONLY the script text (hook through community hook). Nothing else."""

    # Try Anthropic first, then OpenAI
    api_key = get_api_key("anthropic")
    if api_key:
        return _generate_with_anthropic(prompt, story, template_key, api_key)

    api_key = get_api_key("openai")
    if api_key:
        return _generate_with_openai(prompt, story, template_key, api_key)

    raise RuntimeError("No API key found for Anthropic or OpenAI")


def _generate_with_anthropic(prompt: str, story: Story, template_key: str,
                               api_key: str) -> Script:
    """Generate script using Anthropic Claude."""
    body = json.dumps({
        "model": "claude-sonnet-4-6",
        "max_tokens": 500,
        "messages": [{"role": "user", "content": prompt}],
    }).encode()

    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=body,
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode())

    text = data["content"][0]["text"].strip()
    return _build_script(text, story, template_key)


def _generate_with_openai(prompt: str, story: Story, template_key: str,
                            api_key: str) -> Script:
    """Generate script using OpenAI GPT."""
    body = json.dumps({
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 500,
    }).encode()

    req = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode())

    text = data["choices"][0]["message"]["content"].strip()
    return _build_script(text, story, template_key)


def _build_script(text: str, story: Story, template_key: str) -> Script:
    """Build a Script object from generated text.

    Hook-first structure: the LLM output already contains the hook + brand ID +
    body + opinion + community question. We only append the outro.
    """
    # Strip any greeting the LLM may have added despite instructions
    for prefix in [
        "Hey Ninjas!", "Hey ninjas!", "What's up ninjas!",
        "What's up my fellow Ninjas,", "What's up my fellow Ninjas!",
        "I'm Neurodivergent Ninja here back with another video.",
        "This is Neurodivergent Ninja here back with another video.",
    ]:
        if text.startswith(prefix):
            text = text[len(prefix):].strip()

    # Ensure the brand tag is present (LLM sometimes drops it)
    if SHORT_BRAND_ID not in text:
        # Find the end of the first sentence (the hook) and insert brand tag
        first_period = text.find(". ")
        first_excl = text.find("! ")
        first_q = text.find("? ")
        # Find earliest sentence boundary
        ends = [i for i in [first_period, first_excl, first_q] if i > 0]
        if ends:
            insert_at = min(ends) + 2
            text = text[:insert_at] + SHORT_BRAND_ID + " " + text[insert_at:]
        else:
            # Fallback: prepend brand tag
            text = SHORT_BRAND_ID + " " + text

    # Extract hook (everything before brand tag) for the Script object
    brand_idx = text.find(SHORT_BRAND_ID)
    hook = text[:brand_idx].strip() if brand_idx > 0 else text.split(". ")[0]

    # Append outro only (hook is already in the body)
    full_text = f"{text} {STANDARD_OUTRO}"

    words = full_text.split()
    word_count = len(words)
    duration = word_count / WORDS_PER_MINUTE * 60

    return Script(
        title=story.title,
        hook=hook,
        body=text,
        full_text=full_text,
        word_count=word_count,
        estimated_duration_sec=duration,
        source_story=story,
        category=story.category,
        template=template_key,
    )


def generate_from_topic(topic: str, category: str = "tech") -> Script:
    """Generate a script from a custom topic (no RSS story needed)."""
    story = Story(
        title=topic,
        summary=topic,
        url="",
        source="Custom",
        category=category,
    )
    return generate_script_with_llm(story)


# =============================================================================
# Pipeline Integration
# =============================================================================

def run_pipeline(script: Script, output_name: str = None) -> Optional[str]:
    """Feed a script into the ninja video pipeline."""
    pipeline_script = Path(__file__).parent / "ninja-pipeline.sh"
    if not pipeline_script.exists():
        print("❌ Pipeline script not found", file=sys.stderr)
        return None

    if output_name is None:
        slug = re.sub(r'[^a-z0-9]+', '_', script.title.lower())[:30].rstrip('_')
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_name = f"ninja_{slug}_{timestamp}.mp4"

    # Write script to temp file to avoid shell quoting issues with apostrophes etc.
    script_file = Path(tempfile.mktemp(suffix=".txt", prefix="ninja_script_"))
    script_file.write_text(script.full_text)

    cmd = [
        str(pipeline_script),
        "-o", output_name,
        "--file", str(script_file),
    ]

    print(f"\n🎬 Launching pipeline: {output_name}")
    result = subprocess.run(cmd, capture_output=False)

    # Cleanup temp file
    script_file.unlink(missing_ok=True)

    if result.returncode == 0:
        return output_name
    return None


# =============================================================================
# CLI Interface
# =============================================================================

def cmd_discover(args):
    """Discover trending stories."""
    categories = [args.category] if args.category else ["tech", "gaming"]
    print(f"🔍 Fetching stories from: {', '.join(categories)}\n")

    stories = discover_stories(categories)

    if not stories:
        print("❌ No stories found. Check your internet connection.")
        return

    # Group by category
    by_category = {}
    for s in stories:
        by_category.setdefault(s.category, []).append(s)

    for cat, cat_stories in by_category.items():
        print(f"\n{'='*60}")
        print(f"📰 {cat.upper()} ({len(cat_stories)} stories)")
        print(f"{'='*60}")
        for i, story in enumerate(cat_stories[:10], 1):
            print(f"  {i:2d}. [{story.source}] {story.title}")
            if story.summary:
                summary_preview = story.summary[:120]
                if len(story.summary) > 120:
                    summary_preview += "..."
                print(f"      {summary_preview}")
            print()

    print(f"\n📊 Total: {len(stories)} stories across {len(by_category)} categories")

    # Save for reference
    stories_file = Path("/tmp/ninja_discovered_stories.json")
    stories_data = [
        {"index": i, "title": s.title, "summary": s.summary[:200],
         "source": s.source, "url": s.url, "category": s.category}
        for i, s in enumerate(stories)
    ]
    with open(stories_file, "w") as f:
        json.dump(stories_data, f, indent=2)
    print(f"💾 Stories saved to {stories_file}")


def cmd_generate(args):
    """Generate a script from a topic or story index."""
    if args.topic:
        category = args.category or "tech"
        print(f"📝 Generating script for: {args.topic}")
        print(f"   Category: {category}")
        script = generate_from_topic(args.topic, category)
    elif args.story_index is not None:
        stories_file = Path("/tmp/ninja_discovered_stories.json")
        if not stories_file.exists():
            print("❌ Run --discover first to fetch stories", file=sys.stderr)
            sys.exit(1)
        with open(stories_file) as f:
            stories_data = json.load(f)
        if args.story_index >= len(stories_data):
            print(f"❌ Story index {args.story_index} out of range", file=sys.stderr)
            sys.exit(1)
        sd = stories_data[args.story_index]
        story = Story(
            title=sd["title"], summary=sd["summary"], url=sd["url"],
            source=sd["source"], category=sd["category"],
        )
        print(f"📝 Generating script for: {story.title}")
        script = generate_script_with_llm(story)
    else:
        print("❌ Provide --topic or --pick <index>", file=sys.stderr)
        sys.exit(1)

    print(f"\n{'='*60}")
    print(f"🥷 SCRIPT: {script.title}")
    print(f"{'='*60}")
    print(f"📏 {script.word_count} words | ~{script.estimated_duration_sec:.0f}s")
    print(f"🎯 Template: {SCRIPT_TEMPLATES[script.template]['name']}")
    print(f"{'='*60}\n")
    print(script.full_text)
    print(f"\n{'='*60}")

    # Save script
    script_file = Path("/tmp/ninja_latest_script.txt")
    with open(script_file, "w") as f:
        f.write(script.full_text)
    print(f"\n💾 Script saved to {script_file}")

    # Optionally run pipeline
    if args.pipeline:
        run_pipeline(script, args.output)

    return script


def cmd_auto(args):
    """Auto-discover, pick the top story, generate script."""
    categories = [args.category] if args.category else ["tech", "gaming"]
    print(f"🤖 Auto-generating from top story in: {', '.join(categories)}\n")

    stories = discover_stories(categories)
    if not stories:
        print("❌ No stories found.")
        sys.exit(1)

    # Pick the first story (top of feed = most recent/relevant)
    story = stories[0]
    print(f"📰 Selected: [{story.source}] {story.title}\n")

    script = generate_script_with_llm(story)

    print(f"{'='*60}")
    print(f"🥷 SCRIPT: {script.title}")
    print(f"{'='*60}")
    print(f"📏 {script.word_count} words | ~{script.estimated_duration_sec:.0f}s")
    print(f"{'='*60}\n")
    print(script.full_text)
    print(f"\n{'='*60}")

    script_file = Path("/tmp/ninja_latest_script.txt")
    with open(script_file, "w") as f:
        f.write(script.full_text)
    print(f"\n💾 Script saved to {script_file}")

    if args.pipeline:
        run_pipeline(script, args.output)

    return script


def _set_hook(new_hook: str):
    """Override the global hook line."""
    global HOOK_LINE
    HOOK_LINE = new_hook


def main():
    parser = argparse.ArgumentParser(
        description="🥷 Ninja Script Generator — AI-powered content scripts",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    %(prog)s --discover                    # Browse trending stories
    %(prog)s --discover --category gaming  # Gaming stories only
    %(prog)s --topic "NVIDIA RTX 5090"     # Script from custom topic
    %(prog)s --pick 3                      # Script from discovered story #3
    %(prog)s --auto                        # Auto-pick and generate
    %(prog)s --auto --pipeline             # Auto-generate and create video
        """,
    )

    # Modes
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--discover", action="store_true",
                      help="Discover trending stories from RSS feeds")
    mode.add_argument("--topic", type=str,
                      help="Generate script from a custom topic")
    mode.add_argument("--pick", type=int, dest="story_index",
                      help="Generate script from a discovered story (by index)")
    mode.add_argument("--auto", action="store_true",
                      help="Auto-discover and generate from top story")

    # Options
    parser.add_argument("--category", choices=["tech", "gaming", "ai"],
                        help="Filter by content category")
    parser.add_argument("--pipeline", action="store_true",
                        help="Automatically feed script into video pipeline")
    parser.add_argument("--output", "-o", type=str,
                        help="Output video filename (with --pipeline)")
    parser.add_argument("--hook", type=str, default=None,
                        help="Override hook line (default: Hey Ninjas!)")

    args = parser.parse_args()

    # Allow hook override
    if args.hook is not None:
        _set_hook(args.hook)

    if args.discover:
        cmd_discover(args)
    elif args.topic or args.story_index is not None:
        cmd_generate(args)
    elif args.auto:
        cmd_auto(args)


if __name__ == "__main__":
    main()
