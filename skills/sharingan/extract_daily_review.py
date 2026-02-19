#!/usr/bin/env python3
"""Sharingan — Daily Observation Log

Reads ~/.logs/daily-review.log + last 24h of chat history,
extracts today's work summary, and appends to daily-observations.md.

No Claude API calls — this runs daily and is cost-free.
The weekly extract_chat_history.py handles the deep AI synthesis.

Usage:
    python3 extract_daily_review.py [--dry-run]

Cron (daily, 3AM):
    0 3 * * * python3 /home/ndninja/skills/sharingan/extract_daily_review.py >> ~/.logs/sharingan-digest.log 2>&1
"""

import json
import argparse
import re
from collections import Counter
from pathlib import Path
from datetime import datetime, timedelta, timezone

HISTORY_FILE     = Path.home() / ".claude" / "history.jsonl"
DAILY_REVIEW_LOG = Path.home() / ".logs" / "daily-review.log"
SCROLL_DIR       = Path.home() / ".sharingan" / "scrolls"
INDEX_FILE       = Path.home() / ".sharingan" / "index.json"
SCROLL_NAME      = "daily-observations"
SCROLL_PATH      = SCROLL_DIR / f"{SCROLL_NAME}.md"
MAX_DAILY_ENTRIES = 90  # Keep ~3 months of daily entries

SKIP_PREFIXES = {"/exit", "/login", "/model", "/resume", "/help", "/clear",
                 "/sharingan", "/commit", "/review", "/fast"}
MIN_LENGTH = 20

# Patterns that suggest sensitive content — skip these from scrolls / API calls
SENSITIVE_PATTERNS = [
    r"sk-ant-",          # Anthropic keys
    r"sk-[a-zA-Z0-9]{20,}",  # OpenAI-style keys
    r"GOCSPX-",          # Google OAuth secrets
    r"EI[a-zA-Z0-9_-]{30,}",  # ElevenLabs keys
    r"password\s*[:=]",
    r"secret\s*[:=]",
    r"token\s*[:=]\s*['\"]?[a-zA-Z0-9_-]{16,}",
]

import re as _re
_SENSITIVE_RE = _re.compile("|".join(SENSITIVE_PATTERNS), _re.IGNORECASE)

def is_sensitive(text: str) -> bool:
    return bool(_SENSITIVE_RE.search(text))

# Project name extraction — look for known project paths/keywords
PROJECT_PATTERNS = [
    r"glitch", r"spike", r"sharingan", r"sage.?mode", r"dojo", r"ninja-dashboard",
    r"remotion", r"kage.?bunshin", r"shadow.?council", r"prompt.?toolkit",
    r"clawdbot?", r"youtube", r"kling", r"elevenlabs", r"tauri",
]


# ── Logging ────────────────────────────────────────────────────────────────────

def log(msg: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


# ── Chat history (past 24h) ────────────────────────────────────────────────────

def load_recent_chat(hours: int = 24) -> list[str]:
    """Load substantive user messages from the past N hours."""
    if not HISTORY_FILE.exists():
        return []

    cutoff_ms = (datetime.now(timezone.utc) - timedelta(hours=hours)).timestamp() * 1000
    messages = []

    with open(HISTORY_FILE, encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            if entry.get("timestamp", 0) < cutoff_ms:
                continue
            display = entry.get("display", "").strip()
            if len(display) < MIN_LENGTH:
                continue
            if any(display.lower().startswith(p) for p in SKIP_PREFIXES):
                continue
            if is_sensitive(display):
                continue  # Never store API keys / secrets in scrolls
            messages.append(display)

    return messages


# ── Daily review log ───────────────────────────────────────────────────────────

def load_daily_review_events(hours: int = 24) -> list[str]:
    """Extract non-trivial messages from daily-review.log for the past N hours."""
    if not DAILY_REVIEW_LOG.exists():
        return []

    NOISE = {
        "============================================================",
        "Starting Daily Review Automation",
        "No conversations found for analysis",
    }
    cutoff_dt = datetime.now(timezone.utc) - timedelta(hours=hours)
    events = []

    with open(DAILY_REVIEW_LOG, encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue

            try:
                ts = datetime.fromisoformat(entry.get("timestamp", ""))
                if ts < cutoff_dt:
                    continue
            except ValueError:
                continue

            msg = entry.get("message", "").strip()
            if not msg or msg in NOISE:
                continue

            events.append(msg)

    return events


# ── Keyword extraction ─────────────────────────────────────────────────────────

def extract_topics(messages: list[str]) -> list[str]:
    """Pull out the most prominent topics from message text."""
    all_text = " ".join(messages).lower()

    # Count project mentions
    project_hits: Counter = Counter()
    for pat in PROJECT_PATTERNS:
        count = len(re.findall(pat, all_text))
        if count:
            name = pat.replace(".", "").replace("?", "").replace("-", " ").strip()
            project_hits[name] = count

    topics = [name for name, _ in project_hits.most_common(8)]
    return topics


def extract_active_projects(messages: list[str]) -> list[str]:
    """Return project names mentioned in messages."""
    all_text = " ".join(messages).lower()
    found = []
    project_map = {
        "glitch": "Glitch (AuDHD assistant)",
        "spike": "Spike (mood tracker)",
        "sharingan": "Sharingan (self-learning)",
        "sage mode": "Sage Mode (dev team sim)",
        "sagemode": "Sage Mode (dev team sim)",
        "dojo": "The Dojo (content pipeline)",
        "ninja-dashboard": "The Dojo (content pipeline)",
        "remotion": "Remotion video pipeline",
        "kage bunshin": "Kage Bunshin (cluster)",
        "kagebushin": "Kage Bunshin (cluster)",
        "shadow council": "Shadow Council (brainstorm)",
        "prompt toolkit": "Prompt Toolkit",
        "clawdbot": "Clawdbot (Cypher)",
        "youtube": "YouTube content",
        "kling": "Kling avatar pipeline",
        "tauri": "Glitch overlay (Tauri)",
    }
    for key, label in project_map.items():
        if key in all_text and label not in found:
            found.append(label)
    return found


def summarize_messages(messages: list[str], max_items: int = 8) -> list[str]:
    """Return the most informative (longest/richest) messages as representative samples."""
    # Sort by length descending, pick top N
    sorted_msgs = sorted(messages, key=len, reverse=True)
    out = []
    for msg in sorted_msgs[:max_items]:
        snippet = msg[:180] + "…" if len(msg) > 180 else msg
        out.append(snippet)
    return out


# ── Scroll writing ─────────────────────────────────────────────────────────────

SCROLL_HEADER = """\
---
name: {name}
domain: Meta/Workflow
level: 2-tomoe
description: Daily running log of work observations from chat history and daily review. Auto-updated at 3AM.
last_updated: {today}
auto_generated: true
---

# Daily Observations — Running Log

*Auto-updated daily at 3AM by Sharingan. Each entry = one day.*
*For deep weekly synthesis, see the `workflow-insights` scroll.*
"""


def build_day_block(
    today_str: str,
    chat_count: int,
    review_events: list[str],
    topics: list[str],
    projects: list[str],
    samples: list[str],
) -> str:
    lines = [
        f"\n---\n",
        f"## {today_str}",
    ]

    sources = f"chat messages: {chat_count}"
    if review_events:
        sources += f", daily-review events: {len(review_events)}"
    lines.append(f"*{sources}*\n")

    if projects:
        lines.append(f"**Active projects:** {', '.join(projects)}\n")

    if topics:
        lines.append(f"**Topics:** {', '.join(topics)}\n")

    if review_events:
        lines.append("**Daily review events:**")
        for evt in review_events:
            lines.append(f"- {evt}")
        lines.append("")

    if samples:
        lines.append("**Representative messages:**")
        for s in samples:
            lines.append(f"- {s}")
        lines.append("")

    if chat_count == 0 and not review_events:
        lines.append("*No activity recorded.*\n")

    return "\n".join(lines)


def update_scroll(day_block: str, today_str: str):
    """Prepend today's entry to the scroll, capping at MAX_DAILY_ENTRIES."""
    SCROLL_DIR.mkdir(parents=True, exist_ok=True)
    today = datetime.now().strftime("%Y-%m-%d")
    header = SCROLL_HEADER.format(name=SCROLL_NAME, today=today)

    sep = "\n---\n\n## "
    if SCROLL_PATH.exists():
        existing = SCROLL_PATH.read_text(encoding="utf-8")
        if sep in existing:
            body = existing[existing.index(sep):]
        else:
            body = ""
        # Remove today's entry if it already exists (idempotent re-run)
        today_marker = f"\n---\n\n## {today_str}"
        if today_marker in body:
            # Strip the existing today entry and anything up to the next ---
            idx = body.index(today_marker)
            next_sep = body.find("\n---\n", idx + 5)
            if next_sep != -1:
                body = body[next_sep:]
            else:
                body = ""
    else:
        body = ""

    # Cap at MAX_DAILY_ENTRIES by counting separators
    parts = body.split("\n---\n")
    if len(parts) > MAX_DAILY_ENTRIES + 1:
        parts = parts[: MAX_DAILY_ENTRIES + 1]
        body = "\n---\n".join(parts)

    SCROLL_PATH.write_text(header + day_block + body, encoding="utf-8")
    log(f"Scroll written: {SCROLL_PATH}")


def update_index():
    """Upsert daily-observations in index.json."""
    today = datetime.now().strftime("%Y-%m-%d")

    if INDEX_FILE.exists():
        index = json.loads(INDEX_FILE.read_text(encoding="utf-8"))
    else:
        index = {"version": 1, "scrolls": [], "stats": {}}

    index["scrolls"] = [s for s in index["scrolls"] if s["name"] != SCROLL_NAME]
    index["scrolls"].append({
        "name":          SCROLL_NAME,
        "domain":        "Meta/Workflow",
        "level":         "2-tomoe",
        "description":   "Daily running log of work observations from chat history and daily review.",
        "last_updated":  today,
        "keywords":      ["daily", "log", "observations", "workflow", "projects",
                          "activity", "meta", "digest"],
        "can_do_from_cli": True,
        "auto_generated":  True,
    })

    levels = {"1-tomoe": 0, "2-tomoe": 0, "3-tomoe": 0, "mangekyo": 0}
    for s in index["scrolls"]:
        lvl = s.get("level", "1-tomoe")
        if lvl in levels:
            levels[lvl] += 1
    index["stats"] = {"total_scrolls": len(index["scrolls"]), "by_level": levels}

    INDEX_FILE.write_text(json.dumps(index, indent=2), encoding="utf-8")
    log("Index updated.")


# ── Entry point ────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Sharingan daily review digest")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print output, do not write scroll")
    args = parser.parse_args()

    today_str = datetime.now().strftime("%Y-%m-%d")
    log("=" * 50)
    log(f"Sharingan Daily Digest — {today_str}")

    chat_messages  = load_recent_chat(hours=24)
    review_events  = load_daily_review_events(hours=24)

    log(f"Chat messages (24h): {len(chat_messages)}")
    log(f"Daily review events: {len(review_events)}")

    topics   = extract_topics(chat_messages)
    projects = extract_active_projects(chat_messages)
    samples  = summarize_messages(chat_messages)

    if topics:
        log(f"Topics: {', '.join(topics)}")
    if projects:
        log(f"Projects: {', '.join(projects)}")

    day_block = build_day_block(
        today_str    = today_str,
        chat_count   = len(chat_messages),
        review_events= review_events,
        topics       = topics,
        projects     = projects,
        samples      = samples,
    )

    if args.dry_run:
        print("\n" + "─" * 60)
        print(day_block)
        print("─" * 60)
        log("Dry run — nothing written.")
        return

    update_scroll(day_block, today_str)
    update_index()
    log("Done.")


if __name__ == "__main__":
    main()
