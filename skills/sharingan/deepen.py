#!/usr/bin/env python3
"""Sharingan — Scroll Deepening Engine

Takes an existing scroll, discovers new sources via search,
ingests them, and re-synthesizes the scroll at a deeper mastery level.

Usage:
    python3 deepen.py <scroll-name> [--dry-run] [--skip-podcast]
    python3 deepen.py spline-3d-web
    python3 deepen.py remotion-video-code --dry-run
"""

import os
import sys
import json
import shutil
import argparse
import subprocess
import tempfile
import re
from pathlib import Path
from datetime import datetime

# ── Paths ──────────────────────────────────────────────────────────────────────

SKILL_DIR    = Path(os.environ.get("SKILL_DIR", Path(__file__).parent))
SCROLL_DIR   = Path(os.environ.get("SCROLL_DIR", Path.home() / ".sharingan" / "scrolls"))
INDEX_FILE   = Path(os.environ.get("INDEX_FILE", Path.home() / ".sharingan" / "index.json"))
TRAINING_DIR = Path(os.environ.get("TRAINING_DIR", Path.home() / ".sharingan" / "training"))

LEVEL_ORDER   = ["1-tomoe", "2-tomoe", "3-tomoe", "mangekyo-eligible", "mangekyo"]
AUTO_SCROLLS  = {"workflow-insights", "daily-observations"}  # Skip auto-generated

MAX_NEW_SOURCES  = 3   # Max sources to ingest per deepening run
MAX_SCROLL_LINES = 350 # Keep scrolls scannable


# ── Logging ────────────────────────────────────────────────────────────────────

def log(msg: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


# ── API key resolution ─────────────────────────────────────────────────────────

def resolve_api_key() -> str | None:
    """Get Anthropic API key from env or PostgreSQL vault."""
    env_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if env_key and env_key.startswith("sk-ant-api"):
        return env_key

    try:
        result = subprocess.run(
            [
                "psql", "-U", "ndninja", "-d", "api_keys",
                "-t", "-A", "-c",
                "SELECT pgp_sym_decrypt(encrypted_key_pgp, 'ndn-vault-kagebunshin-2026') "
                "FROM keys WHERE service = 'NDN_SHARINGAN' AND status = 'Active' LIMIT 1;",
            ],
            capture_output=True, text=True, timeout=10,
        )
        key = result.stdout.strip()
        if key and key.startswith("sk-ant"):
            log("API key loaded from vault.")
            return key
    except Exception as e:
        log(f"Vault lookup failed: {e}")

    return None


def get_claude_client():
    """Initialize Anthropic client with resolved key."""
    import anthropic
    key = resolve_api_key()
    if not key:
        raise RuntimeError("No valid ANTHROPIC_API_KEY found (env or vault)")
    return anthropic.Anthropic(api_key=key)


# ── Scroll loading ─────────────────────────────────────────────────────────────

def load_scroll(name: str) -> str | None:
    path = SCROLL_DIR / f"{name}.md"
    return path.read_text(encoding="utf-8") if path.exists() else None


def load_index() -> dict:
    if INDEX_FILE.exists():
        return json.loads(INDEX_FILE.read_text(encoding="utf-8"))
    return {"version": 1, "scrolls": [], "stats": {}}


def get_scroll_meta(index: dict, name: str) -> dict | None:
    for s in index.get("scrolls", []):
        if s["name"] == name:
            return s
    return None


def parse_frontmatter(content: str) -> dict:
    """Extract YAML-ish frontmatter from scroll markdown."""
    meta = {}
    if content.startswith("---"):
        end = content.find("---", 3)
        if end != -1:
            block = content[3:end].strip()
            for line in block.split("\n"):
                if ":" in line and not line.strip().startswith("-"):
                    key, val = line.split(":", 1)
                    meta[key.strip()] = val.strip()
    return meta


def extract_existing_sources(content: str) -> list[str]:
    """Pull source URLs from scroll frontmatter."""
    urls = []
    in_sources = False
    for line in content.split("\n"):
        if line.strip().startswith("sources:"):
            in_sources = True
            continue
        if in_sources:
            if line.strip().startswith("- ") or line.strip().startswith("url:"):
                url_match = re.search(r'url:\s*"?([^"\s]+)"?', line)
                if url_match:
                    urls.append(url_match.group(1))
            elif not line.startswith(" ") and not line.startswith("\t") and line.strip():
                in_sources = False
    return urls


# ── Source discovery ───────────────────────────────────────────────────────────

def discover_sources(client, scroll_name: str, scroll_content: str,
                     existing_urls: list[str]) -> list[dict]:
    """Ask Claude to generate search queries, execute them, then pick the best."""

    # Step 1: Generate search queries
    log("Asking Claude for search queries...")
    query_prompt = f"""You are the Sharingan learning system. You need to deepen knowledge about \
a topic by finding NEW sources.

Current scroll name: {scroll_name}
Already-known source URLs: {json.dumps(existing_urls)}

Current scroll content (abbreviated):
{scroll_content[:3000]}

Generate 4-6 search queries to find NEW sources that would deepen this knowledge.
For each, specify the search target.

Focus on:
- Official GitHub repos (libraries, SDKs, tools) not yet studied
- YouTube tutorials covering advanced usage or different angles
- Related tools/libraries that integrate with this topic

Return ONLY a JSON array, no other text:
[{{"query": "search terms here", "target": "github", "reason": "why this adds value"}}, ...]

Targets: "github" or "youtube" only.
Do NOT suggest sources already in the existing URLs list."""

    resp = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=800,
        messages=[{"role": "user", "content": query_prompt}],
    )

    raw = resp.content[0].text.strip()
    # Extract JSON from response (Claude might wrap it in markdown)
    json_match = re.search(r'\[.*\]', raw, re.DOTALL)
    if not json_match:
        log(f"Could not parse search queries from Claude response")
        return []

    try:
        queries = json.loads(json_match.group())
    except json.JSONDecodeError:
        log("Failed to parse search query JSON")
        return []

    log(f"Got {len(queries)} search queries.")

    # Step 2: Execute searches
    all_candidates = []

    for q in queries:
        query = q.get("query", "")
        target = q.get("target", "github")
        reason = q.get("reason", "")

        if target == "github":
            results = search_github(query)
            for r in results:
                url = r.get("url", "")
                if url and url not in existing_urls:
                    all_candidates.append({
                        "type": "github",
                        "url": url,
                        "name": r.get("fullName", ""),
                        "description": r.get("description", ""),
                        "stars": r.get("stargazersCount", 0),
                        "reason": reason,
                    })

        elif target == "youtube":
            results = search_youtube(query)
            for r in results:
                url = r.get("url", "")
                if url and url not in existing_urls:
                    all_candidates.append({
                        "type": "youtube",
                        "url": url,
                        "title": r.get("title", ""),
                        "duration": r.get("duration", ""),
                        "reason": reason,
                    })

    if not all_candidates:
        log("No new source candidates found.")
        return []

    log(f"Found {len(all_candidates)} candidates. Asking Claude to pick the best...")

    # Step 3: Claude picks the best 2-3
    pick_prompt = f"""You are deepening the "{scroll_name}" knowledge scroll.

Here are candidate sources found via search. Pick the {MAX_NEW_SOURCES} BEST ones \
that would add the most NEW knowledge (not duplicate existing content).

Candidates:
{json.dumps(all_candidates, indent=2)}

Already-known URLs (do NOT pick these): {json.dumps(existing_urls)}

Return ONLY a JSON array of the selected sources (same format as input), \
ordered by value. Pick at most {MAX_NEW_SOURCES}."""

    resp = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=600,
        messages=[{"role": "user", "content": pick_prompt}],
    )

    raw = resp.content[0].text.strip()
    json_match = re.search(r'\[.*\]', raw, re.DOTALL)
    if not json_match:
        return all_candidates[:MAX_NEW_SOURCES]

    try:
        picked = json.loads(json_match.group())
        return picked[:MAX_NEW_SOURCES]
    except json.JSONDecodeError:
        return all_candidates[:MAX_NEW_SOURCES]


def search_github(query: str, limit: int = 5) -> list[dict]:
    """Search GitHub repos via gh CLI."""
    try:
        result = subprocess.run(
            ["gh", "search", "repos", query, "--limit", str(limit),
             "--sort", "stars", "--json", "fullName,url,description,stargazersCount"],
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode == 0:
            return json.loads(result.stdout)
    except Exception as e:
        log(f"GitHub search failed: {e}")
    return []


def search_youtube(query: str, limit: int = 3) -> list[dict]:
    """Search YouTube via yt-dlp."""
    try:
        result = subprocess.run(
            ["yt-dlp", "--flat-playlist", f"ytsearch{limit}:{query}",
             "--print", "%(title)s|||%(webpage_url)s|||%(duration_string)s",
             "--no-warnings"],
            capture_output=True, text=True, timeout=30,
        )
        videos = []
        for line in result.stdout.strip().split("\n"):
            if "|||" not in line:
                continue
            parts = line.split("|||")
            if len(parts) >= 2 and parts[1].startswith("http"):
                videos.append({
                    "title": parts[0],
                    "url": parts[1],
                    "duration": parts[2] if len(parts) > 2 else "",
                })
        return videos
    except Exception as e:
        log(f"YouTube search failed: {e}")
    return []


# ── Source ingestion ───────────────────────────────────────────────────────────

def ingest_source(source: dict, work_dir: str) -> str | None:
    """Ingest a single source and return its text content."""
    src_type = source.get("type", "")
    url = source.get("url", "")

    if not url:
        return None

    if src_type == "github":
        return ingest_github(url, work_dir)
    elif src_type == "youtube":
        return ingest_youtube(url, work_dir)
    else:
        log(f"Unknown source type: {src_type}")
        return None


def ingest_github(url: str, work_dir: str) -> str | None:
    """Ingest a GitHub repo via extract_repo.py."""
    log(f"  Ingesting GitHub: {url}")
    try:
        sys.path.insert(0, str(SKILL_DIR))
        from extract_repo import extract
        result = extract(url, work_dir)
        if "error" in result:
            log(f"  GitHub ingest failed: {result['error']}")
            return None

        # Flatten file contents into readable text
        lines = [f"# GitHub Repo: {result.get('repo', url)}"]
        meta = result.get("metadata", {})
        if meta.get("description"):
            lines.append(f"Description: {meta['description']}")
        if meta.get("language"):
            lines.append(f"Language: {meta['language']}")
        if meta.get("topics"):
            lines.append(f"Topics: {', '.join(meta['topics'])}")
        lines.append(f"Files read: {result.get('files_read', 0)} / {result.get('total_files', 0)}")
        lines.append("")

        for f in result.get("files", [])[:30]:  # Cap at 30 files for synthesis
            lines.append(f"## File: {f['path']}")
            content = f["content"][:5000]  # Cap individual file at 5KB for synthesis
            lines.append(content)
            lines.append("")

        return "\n".join(lines)

    except Exception as e:
        log(f"  GitHub ingest error: {e}")
        return None


def ingest_youtube(url: str, work_dir: str) -> str | None:
    """Ingest a YouTube video via extract_transcript.py."""
    log(f"  Ingesting YouTube: {url}")
    try:
        sys.path.insert(0, str(SKILL_DIR))
        from extract_transcript import extract
        result = extract(url, work_dir)
        if "error" in result:
            log(f"  YouTube ingest failed: {result.get('error')}")
            return None

        transcript_path = result.get("transcript_path")
        if transcript_path and Path(transcript_path).exists():
            text = Path(transcript_path).read_text(encoding="utf-8", errors="replace")
            header = (
                f"# YouTube: {result.get('title', 'Unknown')}\n"
                f"Channel: {result.get('channel', 'Unknown')}\n"
                f"Duration: {result.get('duration', 'Unknown')}\n"
                f"Words: {result.get('word_count', 0)}\n\n"
            )
            return header + text[:15000]  # Cap at 15KB for synthesis

        return None

    except Exception as e:
        log(f"  YouTube ingest error: {e}")
        return None


# ── Cross-scroll linking ──────────────────────────────────────────────────────

def find_cross_links(client, scroll_name: str, scroll_content: str,
                     index: dict) -> list[dict]:
    """Find conceptual connections to other scrolls in the vault."""
    other_scrolls = [
        s for s in index.get("scrolls", [])
        if s["name"] != scroll_name and s["name"] not in AUTO_SCROLLS
    ]

    if not other_scrolls:
        return []

    others_summary = json.dumps([
        {"name": s["name"], "domain": s.get("domain", ""), "description": s.get("description", ""),
         "keywords": s.get("keywords", [])}
        for s in other_scrolls
    ], indent=2)

    prompt = f"""Analyze the conceptual connections between scroll "{scroll_name}" and these other scrolls.

{scroll_name} content (abbreviated):
{scroll_content[:2000]}

Other scrolls in vault:
{others_summary}

For each scroll that has a meaningful conceptual connection, explain the relationship.
Return ONLY a JSON array:
[{{"scroll": "name", "relationship": "brief description of how they connect"}}]

Only include scrolls with REAL connections (shared tools, complementary knowledge, \
same ecosystem). Don't force connections. Return [] if none are meaningful."""

    try:
        resp = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = resp.content[0].text.strip()
        json_match = re.search(r'\[.*\]', raw, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
    except Exception as e:
        log(f"Cross-link analysis failed: {e}")

    return []


# ── Re-synthesis ───────────────────────────────────────────────────────────────

def resynthesize(client, scroll_name: str, existing_content: str,
                 new_materials: list[dict], cross_links: list[dict],
                 new_level: str) -> str:
    """Ask Claude to rewrite the scroll incorporating new material."""

    # Build the new sources material block
    materials_text = ""
    for m in new_materials:
        url = m.get("url", "")
        src_type = m.get("type", "")
        content = m.get("content", "")
        materials_text += f"\n\n--- NEW SOURCE: {url} (type: {src_type}) ---\n{content[:8000]}\n"

    # Build cross-links block
    links_text = ""
    if cross_links:
        links_text = "\n\nCross-scroll connections:\n"
        for link in cross_links:
            links_text += f"- {link['scroll']}: {link['relationship']}\n"

    today = datetime.now().strftime("%Y-%m-%d")
    total_sources = len(extract_existing_sources(existing_content)) + len(new_materials)

    prompt = f"""You are the Sharingan learning system. Rewrite this knowledge scroll to \
incorporate new source material, deepening it from its current level to {new_level}.

EXISTING SCROLL:
{existing_content}

NEW SOURCE MATERIAL:
{materials_text}

{links_text}

INSTRUCTIONS:
1. Use the exact scroll template format (frontmatter with ---, then markdown sections)
2. Update the frontmatter:
   - level: {new_level}
   - last_updated: {today}
   - Add new sources to the sources list with today's date
   - sources_count should be {total_sources}
3. SYNTHESIZE — don't just append. Weave new knowledge into existing sections.
4. Add new sections if the new material covers areas the old scroll didn't.
5. Update "Limitations & Gaps" — remove gaps that are now filled, add new ones.
6. If cross-links exist, add a "Related Scrolls" section listing connections.
7. Keep it under {MAX_SCROLL_LINES} lines — lean and scannable.
8. Preserve the honesty protocol — flag single-source claims, uncertainty.
9. If new_level is "mangekyo-eligible", add to frontmatter: mangekyo_eligible: true

Return ONLY the complete scroll markdown. No explanation or wrapping."""

    resp = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=4000,
        messages=[{"role": "user", "content": prompt}],
    )

    return resp.content[0].text.strip()


# ── Level evaluation ───────────────────────────────────────────────────────────

def evaluate_level(current_level: str, total_sources: int,
                   cross_links_count: int) -> str:
    """Determine the new mastery level."""
    current_idx = LEVEL_ORDER.index(current_level) if current_level in LEVEL_ORDER else 0

    if total_sources >= 3 and cross_links_count >= 3:
        new = "mangekyo-eligible"
    elif total_sources >= 3:
        new = "3-tomoe"
    elif total_sources >= 2:
        new = "2-tomoe"
    else:
        new = "1-tomoe"

    new_idx = LEVEL_ORDER.index(new)

    # Never downgrade
    if new_idx <= current_idx and current_level not in ("mangekyo-eligible", "mangekyo"):
        return current_level

    return new


# ── Index update ───────────────────────────────────────────────────────────────

def update_index(scroll_name: str, new_level: str, description: str,
                 keywords: list[str], sources_count: int,
                 cross_links: list[dict]):
    """Update the vault index with new scroll metadata."""
    index = load_index()
    today = datetime.now().strftime("%Y-%m-%d")

    # Remove old entry
    index["scrolls"] = [s for s in index["scrolls"] if s["name"] != scroll_name]

    # Get domain from existing or guess
    entry = {
        "name": scroll_name,
        "level": new_level,
        "description": description,
        "last_updated": today,
        "keywords": keywords,
        "sources_count": sources_count,
        "can_do_from_cli": True,
    }

    if cross_links:
        entry["related_scrolls"] = [l["scroll"] for l in cross_links]

    if new_level == "mangekyo-eligible":
        entry["mangekyo_eligible"] = True

    index["scrolls"].append(entry)

    # Recount stats
    levels = {"1-tomoe": 0, "2-tomoe": 0, "3-tomoe": 0, "mangekyo": 0}
    for s in index["scrolls"]:
        lvl = s.get("level", "1-tomoe")
        if lvl in levels:
            levels[lvl] += 1
        elif lvl == "mangekyo-eligible":
            levels["3-tomoe"] += 1  # Count eligible as 3-tomoe in stats
    index["stats"] = {"total_scrolls": len(index["scrolls"]), "by_level": levels}

    INDEX_FILE.write_text(json.dumps(index, indent=2), encoding="utf-8")


# ── Podcast regeneration ──────────────────────────────────────────────────────

def regenerate_podcast(scroll_name: str):
    """Regenerate the training podcast for the deepened scroll."""
    train_script = SKILL_DIR / "train.py"
    if not train_script.exists():
        log("train.py not found — skipping podcast")
        return

    log(f"Regenerating podcast for {scroll_name}...")
    try:
        result = subprocess.run(
            [sys.executable, str(train_script), scroll_name],
            capture_output=True, text=True, timeout=300,
        )
        if result.returncode == 0:
            log("Podcast regenerated successfully.")
        else:
            log(f"Podcast generation failed: {result.stderr[:200]}")
    except Exception as e:
        log(f"Podcast generation error: {e}")


# ── Main deepening flow ───────────────────────────────────────────────────────

def deepen(scroll_name: str, dry_run: bool = False,
           skip_podcast: bool = False) -> dict:
    """
    Deepen a single scroll.

    Returns:
        {"status": "deepened"|"no_change"|"error"|"already_max",
         "old_level": str, "new_level": str, "sources_added": int}
    """
    log(f"{'[DRY RUN] ' if dry_run else ''}Deepening scroll: {scroll_name}")

    # Load
    content = load_scroll(scroll_name)
    if not content:
        log(f"Scroll not found: {scroll_name}")
        return {"status": "error", "message": "scroll not found"}

    index = load_index()
    meta = get_scroll_meta(index, scroll_name)
    current_level = meta.get("level", "1-tomoe") if meta else "1-tomoe"

    if current_level == "mangekyo":
        log("Already at Mangekyo. Nothing to deepen.")
        return {"status": "already_max", "old_level": "mangekyo", "new_level": "mangekyo"}

    if current_level == "mangekyo-eligible":
        log("Already Mangekyo-eligible. Needs user confirmation to promote.")
        return {"status": "already_max", "old_level": "mangekyo-eligible",
                "new_level": "mangekyo-eligible"}

    existing_urls = extract_existing_sources(content)
    log(f"Current level: {current_level} | Existing sources: {len(existing_urls)}")

    # Initialize Claude
    client = get_claude_client()

    # Discover new sources
    sources = discover_sources(client, scroll_name, content, existing_urls)
    if not sources:
        log("No new sources discovered. Scroll may be at maximum depth for available material.")
        return {"status": "no_change", "old_level": current_level,
                "new_level": current_level, "sources_added": 0}

    log(f"Selected {len(sources)} new sources to ingest:")
    for s in sources:
        log(f"  [{s.get('type')}] {s.get('url', '')} — {s.get('reason', '')}")

    if dry_run:
        log("Dry run — stopping before ingestion.")
        return {"status": "dry_run", "old_level": current_level,
                "sources_found": len(sources)}

    # Ingest sources
    ingested = []
    with tempfile.TemporaryDirectory(prefix="sharingan_deepen_") as work_dir:
        for source in sources:
            text = ingest_source(source, work_dir)
            if text:
                ingested.append({
                    "type": source.get("type", ""),
                    "url": source.get("url", ""),
                    "content": text,
                })
                log(f"  Ingested: {source.get('url', '')} ({len(text)} chars)")
            else:
                log(f"  Failed to ingest: {source.get('url', '')}")

    if not ingested:
        log("All source ingestions failed.")
        return {"status": "error", "message": "all ingestions failed",
                "old_level": current_level}

    # Cross-link analysis
    log("Analyzing cross-scroll connections...")
    cross_links = find_cross_links(client, scroll_name, content, index)
    if cross_links:
        log(f"Found {len(cross_links)} cross-links:")
        for link in cross_links:
            log(f"  → {link['scroll']}: {link['relationship']}")

    # Evaluate new level
    total_sources = len(existing_urls) + len(ingested)
    new_level = evaluate_level(current_level, total_sources, len(cross_links))
    leveled_up = LEVEL_ORDER.index(new_level) > LEVEL_ORDER.index(current_level)

    if leveled_up:
        log(f"LEVEL UP: {current_level} → {new_level}")
    else:
        log(f"Level stays at {current_level} (more sources needed for next tier)")
        new_level = current_level  # Don't change level text if not leveling up

    # Re-synthesize
    log("Re-synthesizing scroll with new material...")
    new_content = resynthesize(
        client, scroll_name, content, ingested, cross_links, new_level
    )

    if not new_content or len(new_content) < 100:
        log("Re-synthesis produced empty/short result. Keeping original.")
        return {"status": "error", "message": "synthesis failed",
                "old_level": current_level}

    # Backup old scroll
    backup_path = SCROLL_DIR / f"{scroll_name}.md.bak"
    (SCROLL_DIR / f"{scroll_name}.md").rename(backup_path)

    # Write new scroll
    scroll_path = SCROLL_DIR / f"{scroll_name}.md"
    scroll_path.write_text(new_content, encoding="utf-8")
    log(f"Scroll updated: {scroll_path}")
    log(f"Backup saved: {backup_path}")

    # Extract description and keywords from new content for index
    fm = parse_frontmatter(new_content)
    description = fm.get("description", meta.get("description", "") if meta else "")
    keywords = meta.get("keywords", []) if meta else []
    domain = fm.get("domain", meta.get("domain", "") if meta else "")

    # Update index
    entry_data = {
        "name": scroll_name,
        "level": new_level,
        "description": description,
        "keywords": keywords,
        "sources_count": total_sources,
        "cross_links": cross_links,
    }
    if domain:
        entry_data["domain"] = domain
    update_index(scroll_name, new_level, description, keywords,
                 total_sources, cross_links)
    log("Index updated.")

    # Regenerate podcast if leveled up
    if leveled_up and not skip_podcast:
        regenerate_podcast(scroll_name)

    result = {
        "status": "deepened",
        "old_level": current_level,
        "new_level": new_level,
        "sources_added": len(ingested),
        "total_sources": total_sources,
        "cross_links": len(cross_links),
        "leveled_up": leveled_up,
    }

    if new_level == "mangekyo-eligible":
        log("★ MANGEKYO ELIGIBLE — awaiting user confirmation to promote.")
        result["mangekyo_eligible"] = True

    log(f"Deepening complete: {json.dumps(result)}")
    return result


# ── Entry point ────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Sharingan scroll deepening")
    parser.add_argument("scroll", help="Name of the scroll to deepen")
    parser.add_argument("--dry-run", action="store_true",
                        help="Discover sources but don't ingest or rewrite")
    parser.add_argument("--skip-podcast", action="store_true",
                        help="Skip podcast regeneration after leveling up")
    args = parser.parse_args()

    log("=" * 50)
    result = deepen(args.scroll, dry_run=args.dry_run,
                    skip_podcast=args.skip_podcast)
    log("=" * 50)

    if result.get("status") == "error":
        sys.exit(1)


if __name__ == "__main__":
    main()
