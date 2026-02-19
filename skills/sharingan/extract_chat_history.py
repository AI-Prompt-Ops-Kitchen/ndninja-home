#!/usr/bin/env python3
"""Sharingan — Weekly Chat History Digest

Reads ~/.claude/history.jsonl, synthesizes the past week's conversations
into actionable insights, and writes/updates the workflow-insights scroll.

Usage:
    python3 extract_chat_history.py [--days 7] [--dry-run]

Cron (weekly, Sunday 3AM):
    0 3 * * 0 python3 /home/ndninja/skills/sharingan/extract_chat_history.py >> ~/.logs/sharingan-digest.log 2>&1
"""

import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime, timedelta, timezone

HISTORY_FILE  = Path.home() / ".claude" / "history.jsonl"
SCROLL_DIR    = Path.home() / ".sharingan" / "scrolls"
INDEX_FILE    = Path.home() / ".sharingan" / "index.json"
SCROLL_NAME   = "workflow-insights"
SCROLL_PATH   = SCROLL_DIR / f"{SCROLL_NAME}.md"

# Slash commands and short entries that carry no signal
SKIP_PREFIXES = {"/exit", "/login", "/model", "/resume", "/help", "/clear",
                 "/sharingan", "/commit", "/review", "/fast"}
MIN_LENGTH = 20

# Patterns that suggest sensitive content — never send these to the API or store in scrolls
import re as _re
_SENSITIVE_RE = _re.compile(
    r"sk-ant-|sk-[a-zA-Z0-9]{20,}|GOCSPX-|EI[a-zA-Z0-9_-]{30,}"
    r"|password\s*[:=]|secret\s*[:=]|token\s*[:=]\s*['\"]?[a-zA-Z0-9_-]{16,}",
    _re.IGNORECASE,
)

def is_sensitive(text: str) -> bool:
    return bool(_SENSITIVE_RE.search(text))


# ── Logging ────────────────────────────────────────────────────────────────────

def log(msg: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


# ── History loading ────────────────────────────────────────────────────────────

def load_history(days: int) -> list[dict]:
    """Load substantive chat entries from the past N days."""
    if not HISTORY_FILE.exists():
        log(f"ERROR: History file not found: {HISTORY_FILE}")
        return []

    cutoff_ms = (datetime.now(timezone.utc) - timedelta(days=days)).timestamp() * 1000
    entries = []

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
                continue  # Never store API keys / secrets in scrolls or send to API

            entries.append({
                "display":   display,
                "timestamp": entry["timestamp"],
                "project":   entry.get("project", ""),
                "sessionId": entry.get("sessionId", ""),
            })

    return entries


def group_by_day(entries: list[dict]) -> dict[str, list[str]]:
    """Group message text by date (UTC)."""
    days: dict[str, list[str]] = {}
    for e in entries:
        dt  = datetime.fromtimestamp(e["timestamp"] / 1000, tz=timezone.utc)
        key = dt.strftime("%Y-%m-%d")
        days.setdefault(key, []).append(e["display"])
    return days


# ── Synthesis ──────────────────────────────────────────────────────────────────

def synthesize_with_claude(grouped: dict[str, list[str]], week_label: str) -> str:
    """Send the week's messages to Claude haiku for insight synthesis."""
    try:
        import anthropic
    except ImportError:
        log("anthropic SDK not installed — pip install anthropic")
        return fallback_summarize(grouped)

    lines = []
    for day, messages in sorted(grouped.items()):
        lines.append(f"\n### {day}")
        for msg in messages:
            snippet = msg[:500] + "…" if len(msg) > 500 else msg
            lines.append(f"- {snippet}")

    conversation_dump = "\n".join(lines)
    total = sum(len(v) for v in grouped.values())

    prompt = f"""You are analyzing a week of Claude Code chat history for Neurodivergent Ninja \
(AuDHD developer, he/him). These are his messages from coding sessions during {week_label}.

{conversation_dump}

From these {total} messages, extract and synthesize:

1. **Technical Decisions Made** — Specific architectural choices, tech selections, design decisions
2. **Problems Solved** — Bugs, blockers, and how they were resolved
3. **Tools & Scripts Built** — New things created (be specific: file names, project names)
4. **Recurring Patterns** — Themes appearing across multiple sessions
5. **Gotchas & Lessons** — Things that tripped up or required multiple attempts
6. **Active Projects** — Which projects were touched and what direction they moved

Rules:
- Be specific and concrete — file names, tool names, and decisions matter
- Skip sections where there's no real data rather than writing vague filler
- Keep each bullet tight — max 2 lines each
- Do NOT hallucinate — only state what's clearly evidenced in the messages"""

    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    resp = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}],
    )
    return resp.content[0].text


def fallback_summarize(grouped: dict[str, list[str]]) -> str:
    """Keyword-only summary when the API is unavailable."""
    lines = ["> *[No Claude API — keyword summary only. Set ANTHROPIC_API_KEY for full synthesis.]*\n"]
    for day, messages in sorted(grouped.items()):
        lines.append(f"### {day} ({len(messages)} messages)")
        for msg in messages[:8]:
            lines.append(f"- {msg[:200]}")
    return "\n".join(lines)


# ── Scroll writing ─────────────────────────────────────────────────────────────

SCROLL_HEADER = """\
---
name: {name}
domain: Meta/Workflow
level: mangekyo
description: Auto-synthesized weekly insights from Claude Code chat history. Living document.
last_updated: {today}
auto_generated: true
---

# Workflow Insights — Living Digest

*Auto-updated weekly by Sharingan chat digest. Each section = one week of sessions.*
"""

def update_scroll(synthesis: str, week_label: str, total: int):
    """Prepend this week's entry to the scroll, preserving older weeks."""
    SCROLL_DIR.mkdir(parents=True, exist_ok=True)
    today = datetime.now().strftime("%Y-%m-%d")

    week_block = (
        f"\n---\n\n"
        f"## Week of {week_label}\n"
        f"*{total} conversations analyzed · Generated {today}*\n\n"
        f"{synthesis}\n"
    )

    if SCROLL_PATH.exists():
        existing = SCROLL_PATH.read_text(encoding="utf-8")
        sep = "\n---\n\n## Week of "
        if sep in existing:
            body = existing[existing.index(sep):]
            # Deduplicate: remove ALL existing entries for this exact week_label
            this_marker = f"\n---\n\n## Week of {week_label}\n"
            while this_marker in body:
                idx = body.index(this_marker)
                next_idx = body.find("\n---\n\n## Week of ", idx + len(this_marker))
                if next_idx != -1:
                    body = body[:idx] + body[next_idx:]
                else:
                    body = body[:idx]
                    break
        else:
            body = ""
    else:
        body = ""

    header = SCROLL_HEADER.format(name=SCROLL_NAME, today=today)
    SCROLL_PATH.write_text(header + week_block + body, encoding="utf-8")
    log(f"Scroll written: {SCROLL_PATH}")


def update_index(total: int):
    """Upsert the workflow-insights entry in index.json."""
    today = datetime.now().strftime("%Y-%m-%d")

    if INDEX_FILE.exists():
        index = json.loads(INDEX_FILE.read_text(encoding="utf-8"))
    else:
        index = {"version": 1, "scrolls": [], "stats": {}}

    # Remove stale entry
    index["scrolls"] = [s for s in index["scrolls"] if s["name"] != SCROLL_NAME]
    index["scrolls"].append({
        "name":          SCROLL_NAME,
        "domain":        "Meta/Workflow",
        "level":         "mangekyo",
        "description":   "Auto-synthesized weekly insights from Claude Code chat history.",
        "last_updated":  today,
        "keywords":      ["workflow", "decisions", "patterns", "weekly", "digest",
                          "chat", "insights", "meta", "lessons", "projects"],
        "sources_count": total,
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


# ── API key resolution ─────────────────────────────────────────────────────────

def resolve_api_key() -> str | None:
    """
    Get a working Anthropic API key.
    Priority: env var (if it looks like a real key) → PostgreSQL vault.
    OAuth tokens (sk-ant-oat01-...) are NOT API keys — skip them.
    """
    import subprocess

    env_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if env_key and env_key.startswith("sk-ant-api"):
        return env_key  # Looks like a real API key

    # Try vault (NDN_SHARINGAN entry)
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
            log("API key loaded from vault (NDN_SHARINGAN).")
            return key
    except Exception as e:
        log(f"Vault lookup failed: {e}")

    return None


# ── Entry point ────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Sharingan weekly chat digest")
    parser.add_argument("--days", type=int, default=7,
                        help="Days of history to analyze (default: 7)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print synthesis, do not write scroll")
    args = parser.parse_args()

    cutoff_dt  = datetime.now() - timedelta(days=args.days)
    week_label = f"{cutoff_dt.strftime('%b %d')} – {datetime.now().strftime('%b %d, %Y')}"

    log("=" * 50)
    log(f"Sharingan Chat Digest — {week_label}")
    log(f"Lookback: {args.days} days")

    entries = load_history(args.days)
    if not entries:
        log("No substantive messages in window. Nothing to digest.")
        return

    grouped = group_by_day(entries)
    total   = sum(len(v) for v in grouped.values())
    log(f"Found {total} messages across {len(grouped)} days.")

    api_key = resolve_api_key()
    if api_key:
        os.environ["ANTHROPIC_API_KEY"] = api_key
        log("Synthesizing with Claude haiku…")
        try:
            synthesis = synthesize_with_claude(grouped, week_label)
        except Exception as e:
            log(f"Claude failed ({e}) — falling back to keyword mode")
            synthesis = fallback_summarize(grouped)
    else:
        log("No valid ANTHROPIC_API_KEY — keyword fallback")
        synthesis = fallback_summarize(grouped)

    if args.dry_run:
        print("\n" + "─" * 60)
        print(synthesis)
        print("─" * 60)
        log("Dry run — nothing written.")
        return

    update_scroll(synthesis, week_label, total)
    update_index(total)
    log("Done.")


if __name__ == "__main__":
    main()
