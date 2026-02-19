#!/usr/bin/env python3
"""Sharingan — Autonomous Learning Loop

Picks the weakest scroll in the vault, deepens it automatically,
and logs results. Designed to run unattended via cron.

Usage:
    python3 autolearn.py                     # Auto-pick weakest scroll
    python3 autolearn.py --scroll <name>     # Deepen a specific scroll
    python3 autolearn.py --dry-run           # Preview without changes
    python3 autolearn.py --all               # Deepen all eligible scrolls (one level each)

Cron (weekly, Sunday 4AM — after digest finishes):
    0 4 * * 0 python3 /home/ndninja/skills/sharingan/autolearn.py >> ~/.logs/sharingan-autolearn.log 2>&1
"""

import sys
import json
import argparse
from pathlib import Path
from datetime import datetime

SKILL_DIR  = Path(__file__).parent
INDEX_FILE = Path.home() / ".sharingan" / "index.json"

# Scrolls that should never be auto-deepened
SKIP_SCROLLS = {"workflow-insights", "daily-observations"}

# Level priority (lower index = weaker = deepen first)
LEVEL_ORDER = ["1-tomoe", "2-tomoe", "3-tomoe", "mangekyo-eligible", "mangekyo"]


def log(msg: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


def load_index() -> dict:
    if INDEX_FILE.exists():
        return json.loads(INDEX_FILE.read_text(encoding="utf-8"))
    return {"version": 1, "scrolls": [], "stats": {}}


def pick_weakest(index: dict) -> str | None:
    """Find the scroll most in need of deepening.

    Priority:
    1. Lowest mastery level
    2. Among same level, oldest last_updated
    3. Skip auto-generated and already-maxed scrolls
    """
    candidates = [
        s for s in index.get("scrolls", [])
        if s["name"] not in SKIP_SCROLLS
        and s.get("level") not in ("mangekyo", "mangekyo-eligible")
        and not s.get("auto_generated", False)
    ]

    if not candidates:
        return None

    def sort_key(s):
        level = s.get("level", "1-tomoe")
        level_idx = LEVEL_ORDER.index(level) if level in LEVEL_ORDER else 0
        updated = s.get("last_updated", "2000-01-01")
        return (level_idx, updated)

    candidates.sort(key=sort_key)
    return candidates[0]["name"]


def get_all_eligible(index: dict) -> list[str]:
    """Get all scrolls eligible for deepening."""
    return [
        s["name"] for s in index.get("scrolls", [])
        if s["name"] not in SKIP_SCROLLS
        and s.get("level") not in ("mangekyo", "mangekyo-eligible")
        and not s.get("auto_generated", False)
    ]


def run_deepen(scroll_name: str, dry_run: bool = False) -> dict:
    """Import and run deepen on a scroll."""
    sys.path.insert(0, str(SKILL_DIR))
    from deepen import deepen
    return deepen(scroll_name, dry_run=dry_run, skip_podcast=True)


def main():
    parser = argparse.ArgumentParser(description="Sharingan autonomous learning")
    parser.add_argument("--scroll", type=str, default=None,
                        help="Deepen a specific scroll (default: auto-pick weakest)")
    parser.add_argument("--all", action="store_true",
                        help="Deepen ALL eligible scrolls (one level each)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Preview without making changes")
    args = parser.parse_args()

    log("=" * 60)
    log("Sharingan Autolearn — Autonomous Deepening Loop")
    log("=" * 60)

    index = load_index()
    total = len([s for s in index.get("scrolls", []) if s["name"] not in SKIP_SCROLLS
                 and not s.get("auto_generated")])

    log(f"Vault: {total} knowledge scrolls")

    # Show vault status
    for s in index.get("scrolls", []):
        if s["name"] in SKIP_SCROLLS or s.get("auto_generated"):
            continue
        level = s.get("level", "?")
        name = s["name"]
        log(f"  [{level:>18}] {name}")

    log("")

    if args.all:
        # Deepen everything eligible
        targets = get_all_eligible(index)
        if not targets:
            log("No scrolls eligible for deepening.")
            return

        log(f"Deepening {len(targets)} scrolls...")
        results = []
        for name in targets:
            log(f"\n{'─' * 40}")
            result = run_deepen(name, dry_run=args.dry_run)
            results.append({"scroll": name, **result})

        # Summary
        log(f"\n{'═' * 60}")
        log("AUTOLEARN SUMMARY")
        log(f"{'═' * 60}")
        for r in results:
            status = r.get("status", "?")
            old = r.get("old_level", "?")
            new = r.get("new_level", "?")
            added = r.get("sources_added", 0)
            if r.get("leveled_up"):
                log(f"  ★ {r['scroll']}: {old} → {new} (+{added} sources)")
            else:
                log(f"    {r['scroll']}: {status} (stayed at {old})")

    else:
        # Single scroll
        if args.scroll:
            target = args.scroll
            # Verify it exists
            meta = next((s for s in index.get("scrolls", []) if s["name"] == target), None)
            if not meta:
                log(f"Scroll not found: {target}")
                log(f"Available: {', '.join(s['name'] for s in index.get('scrolls', []))}")
                sys.exit(1)
        else:
            target = pick_weakest(index)
            if not target:
                log("No scrolls eligible for deepening. All at max level or vault is empty.")
                return
            log(f"Auto-selected weakest scroll: {target}")

        log(f"\n{'─' * 40}")
        result = run_deepen(target, dry_run=args.dry_run)

        # Summary
        log(f"\n{'═' * 60}")
        status = result.get("status", "?")
        if result.get("leveled_up"):
            old = result.get("old_level", "?")
            new = result.get("new_level", "?")
            added = result.get("sources_added", 0)
            links = result.get("cross_links", 0)
            log(f"★ LEVEL UP: {target}: {old} → {new}")
            log(f"  Sources added: {added} | Cross-links: {links}")
            if result.get("mangekyo_eligible"):
                log(f"  ★ MANGEKYO ELIGIBLE — say '/sharingan promote {target}' to confirm")
        elif status == "no_change":
            log(f"No new sources found for {target}. Try again later.")
        elif status == "deepened":
            log(f"Scroll deepened with {result.get('sources_added', 0)} new sources (level unchanged)")
        elif status == "already_max":
            log(f"{target} is already at {result.get('old_level', '?')}")
        elif status == "error":
            log(f"Error: {result.get('message', 'unknown')}")
        else:
            log(f"Result: {json.dumps(result)}")

        log(f"{'═' * 60}")


if __name__ == "__main__":
    main()
