#!/usr/bin/env python3
"""
Daily Review Automation Script
Analyzes recent Claude Code conversations and generates improvement suggestions.

Features:
- Cross-run dedup: skips suggestions that already exist as pending/in_progress
- Tooling dedup: skips suggestions for already-installed skills/plugins
- Intake throttling: caps new suggestions per run (default 10)
- Parameterized SQL: no string interpolation in queries
- Dry-run mode: --dry-run to preview without inserting
"""

import os
import sys
import json
import subprocess
import re
import argparse
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta
from pathlib import Path
from lib.structured_logger import get_logger, get_correlation_id

logger = get_logger("daily-review")

# Constants
MAX_NEW_SUGGESTIONS = 10
SKILLS_DIR = Path.home() / '.claude' / 'skills'
PLUGINS_JSON = Path.home() / '.claude' / 'plugins' / 'installed_plugins.json'
PRIORITY_ORDER = {'high': 0, 'medium': 1, 'low': 2}

# Database configurations
CLAUDE_MEMORY_DB = {
    'host': 'localhost',
    'port': 5432,
    'database': 'claude_memory',
    'user': 'claude_mcp',
    'password': 'REDACTED'
}

WORKSPACE_DB = {
    'host': '/var/run/postgresql',
    'database': 'workspace',
    'user': 'ndninja',
}


def get_db_connection(db='claude_memory'):
    """Create database connection."""
    if db == 'workspace':
        return psycopg2.connect(**WORKSPACE_DB)
    else:
        return psycopg2.connect(**CLAUDE_MEMORY_DB)


def fetch_recent_conversations(days=1):
    """Fetch conversation summaries from the past N days."""
    logger.info(f"Fetching conversations from past {days} day(s)...")

    with get_db_connection('claude_memory') as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT
                    session_id,
                    summary,
                    action_items,
                    key_decisions,
                    topics_discussed,
                    emotional_context,
                    created_at
                FROM conversation_summaries
                WHERE created_at >= NOW() - INTERVAL '%s days'
                  AND app_source = 'code'
                ORDER BY created_at DESC;
            """, (days,))

            results = cur.fetchall()
            logger.info(f"Found {len(results)} conversations")
            return results


def fetch_existing_suggestions():
    """Fetch titles of all pending/in_progress suggestions for cross-run dedup."""
    logger.info("Fetching existing active suggestions...")

    with get_db_connection('workspace') as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT lower(title) FROM skill_suggestions
                WHERE status IN ('pending', 'in_progress');
            """)
            titles = {row[0] for row in cur.fetchall()}
            logger.info(f"Found {len(titles)} existing active suggestions")
            return titles


def fetch_installed_tooling():
    """Build a set of installed skill/plugin names for tooling dedup."""
    tool_names = set()

    # Collect skill names from ~/.claude/skills/
    if SKILLS_DIR.is_dir():
        for f in SKILLS_DIR.iterdir():
            if f.is_file() and f.suffix == '.md':
                tool_names.add(f.stem.lower())
            elif f.is_dir():
                tool_names.add(f.name.lower())

    # Collect plugin names from installed_plugins.json
    if PLUGINS_JSON.is_file():
        try:
            data = json.loads(PLUGINS_JSON.read_text())
            for key in data.get('plugins', {}):
                # Keys look like "frontend-design@claude-plugins-official"
                plugin_name = key.split('@')[0].lower()
                tool_names.add(plugin_name)
        except (json.JSONDecodeError, KeyError):
            logger.warning("Could not parse installed_plugins.json")

    logger.info(f"Found {len(tool_names)} installed tools (skills + plugins)")
    return tool_names


def dedup_against_existing(suggestions, existing_titles, installed_tools):
    """Filter suggestions against existing active items and installed tooling.

    Returns (filtered_list, report_dict).
    """
    filtered = []
    skipped_existing = []
    skipped_tooling = []

    for suggestion in suggestions:
        title = suggestion.get('title', '')
        title_lower = title.lower()

        # Check 1: exact title match against pending/in_progress
        if title_lower in existing_titles:
            skipped_existing.append(title)
            logger.info(f"  DEDUP (existing): {title}")
            continue

        # Check 2: does the title reference an already-installed tool?
        matched_tool = None
        for tool_name in installed_tools:
            # Only match tool names of 4+ chars to avoid false positives
            if len(tool_name) >= 4 and tool_name in title_lower:
                matched_tool = tool_name
                break

        if matched_tool:
            skipped_tooling.append((title, matched_tool))
            logger.info(f"  DEDUP (installed '{matched_tool}'): {title}")
            continue

        filtered.append(suggestion)

    report = {
        'skipped_existing': skipped_existing,
        'skipped_tooling': skipped_tooling,
        'kept': len(filtered),
    }
    return filtered, report


def throttle_suggestions(suggestions, max_count=MAX_NEW_SUGGESTIONS):
    """Cap the number of suggestions, keeping highest priority first."""
    if len(suggestions) <= max_count:
        return suggestions, []

    # Sort by priority (high first), then keep top N
    sorted_suggestions = sorted(
        suggestions,
        key=lambda s: PRIORITY_ORDER.get(s.get('priority', 'low'), 2)
    )
    kept = sorted_suggestions[:max_count]
    throttled = sorted_suggestions[max_count:]

    for s in throttled:
        logger.info(f"  THROTTLED: {s.get('title')} (priority={s.get('priority', 'medium')})")

    return kept, throttled


def analyze_with_council(conversations):
    """Send conversations to LLM Council for analysis."""
    logger.info("Analyzing conversations with LLM Council...")

    # Format conversations for analysis
    conv_data = []
    for conv in conversations:
        conv_data.append({
            'session_id': conv['session_id'],
            'summary': conv['summary'],
            'action_items': conv['action_items'],
            'key_decisions': conv['key_decisions'],
            'topics_discussed': conv['topics_discussed'],
            'emotional_context': conv['emotional_context'],
            'date': conv['created_at'].isoformat() if conv['created_at'] else None
        })

    # Create analysis prompt
    prompt = f"""Analyze these Claude Code conversation summaries to identify patterns and suggest improvements.

CONVERSATION DATA:
{json.dumps(conv_data, indent=2)}

Your task:
1. Identify repeated user requests or pain points (e.g., "user asked to export docs 3 times this week")
2. Suggest specific improvements:
   - NEW SKILLS: Commands that would help repeated workflows (e.g., /export-docs)
   - PLUGINS: Functionality that needs persistent state or complex orchestration
   - ARCHITECTURE: System improvements (e.g., "add caching layer for API calls")
   - OPTIMIZATIONS: Performance or UX improvements

For each suggestion, provide:
- type: skill|plugin|architecture|optimization
- title: Brief, actionable title (e.g., "Create /export-docs skill")
- rationale: Why this matters (include evidence: "appeared in 3/5 sessions")
- implementation_notes: Technical approach (e.g., "Use Craft MCP, accept format param")
- priority: high|medium|low (high = 3+ occurrences or major pain point)

Return ONLY a valid JSON array of suggestion objects, nothing else. Example:
[
  {{
    "type": "skill",
    "title": "Create /example skill",
    "rationale": "User requested this 3 times",
    "implementation_notes": "Use X approach",
    "priority": "high"
  }}
]
"""

    # Call LLM Council
    try:
        result = subprocess.run(
            ['python3', '/home/ndninja/projects/llm-council/council.py', prompt],
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )

        if result.returncode != 0:
            logger.error(f"LLM Council failed: {result.stderr}")
            return []

        # Parse council output
        # The council saves to /tmp/council_result.json
        try:
            with open('/tmp/council_result.json', 'r') as f:
                council_data = json.load(f)

                all_suggestions = []

                for model, response in council_data.get('individual_responses', {}).items():
                    logger.info(f"Parsing {model} response...")

                    # Look for JSON array in response
                    match = re.search(r'(\[[\s\S]*?\])', response)
                    if match:
                        try:
                            model_suggestions = json.loads(match.group(1))
                            logger.info(f"  Found {len(model_suggestions)} suggestions from {model}")
                            all_suggestions.extend(model_suggestions)
                        except json.JSONDecodeError:
                            logger.warning(f"  {model} response contains [ but not valid JSON")
                            continue
                    else:
                        logger.warning(f"  No JSON array found in {model} response")

                if not all_suggestions:
                    logger.warning("No suggestions extracted from any model")
                    return []

                # Deduplicate suggestions by title within this run (case-insensitive)
                seen_titles = set()
                unique_suggestions = []
                for suggestion in all_suggestions:
                    title_lower = suggestion.get('title', '').lower()
                    if title_lower and title_lower not in seen_titles:
                        seen_titles.add(title_lower)
                        unique_suggestions.append(suggestion)

                logger.info(f"Total suggestions: {len(all_suggestions)} ({len(unique_suggestions)} unique within run)")
                return unique_suggestions

        except FileNotFoundError:
            logger.error("Council result file not found")
            return []
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse council JSON: {e}")
            return []

    except subprocess.TimeoutExpired:
        logger.error("LLM Council timed out")
        return []
    except Exception as e:
        logger.error(f"Error calling LLM Council: {e}")
        return []


def insert_suggestions(suggestions, source_session=None, dry_run=False):
    """Insert suggestions into skill_suggestions table using parameterized queries.

    Uses ON CONFLICT DO NOTHING to gracefully handle the partial unique index.
    """
    if not suggestions:
        logger.info("No suggestions to insert")
        return 0

    action = "DRY RUN - would insert" if dry_run else "Inserting"
    logger.info(f"{action} {len(suggestions)} suggestions into workspace database...")

    if dry_run:
        for s in suggestions:
            logger.info(f"  [DRY RUN] {s.get('title')} (priority={s.get('priority', 'medium')})")
        return len(suggestions)

    inserted_count = 0
    skipped_conflict = 0
    session = source_session or 'automated-daily-review'

    # Validate suggestion_type values
    valid_types = {'skill', 'plugin', 'tool', 'memory', 'workflow', 'architecture', 'optimization'}

    with get_db_connection('workspace') as conn:
        with conn.cursor() as cur:
            for suggestion in suggestions:
                try:
                    stype = suggestion.get('type', 'optimization')
                    if stype not in valid_types:
                        stype = 'optimization'

                    priority = suggestion.get('priority', 'medium')
                    if priority not in ('high', 'medium', 'low'):
                        priority = 'medium'

                    cur.execute("""
                        INSERT INTO skill_suggestions (
                            source_session, source_date, suggestion_type,
                            title, rationale, implementation_notes,
                            priority, status
                        ) VALUES (%s, CURRENT_DATE, %s, %s, %s, %s, %s, 'pending')
                        ON CONFLICT ((lower(title))) WHERE status IN ('pending', 'in_progress')
                        DO NOTHING;
                    """, (
                        session,
                        stype,
                        suggestion.get('title', 'Untitled suggestion'),
                        suggestion.get('rationale', ''),
                        suggestion.get('implementation_notes', ''),
                        priority,
                    ))

                    if cur.rowcount == 1:
                        inserted_count += 1
                        logger.info(f"  Inserted: {suggestion.get('title')}")
                    else:
                        skipped_conflict += 1
                        logger.info(f"  CONFLICT (DB index): {suggestion.get('title')}")

                except Exception as e:
                    logger.error(f"  Failed to insert '{suggestion.get('title', 'unknown')}': {e}")
                    conn.rollback()
                    continue

            conn.commit()

    logger.info(f"Inserted {inserted_count}/{len(suggestions)} (skipped {skipped_conflict} conflicts)")
    return inserted_count


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(description='Daily Review Automation')
    parser.add_argument('days', nargs='?', type=int, default=1,
                        help='Number of days of history to analyze (default: 1)')
    parser.add_argument('--dry-run', action='store_true',
                        help='Preview what would be inserted without writing to DB')
    parser.add_argument('--max-suggestions', type=int, default=MAX_NEW_SUGGESTIONS,
                        help=f'Max new suggestions per run (default: {MAX_NEW_SUGGESTIONS})')
    args = parser.parse_args()

    logger.info("=" * 60)
    logger.info("Starting Daily Review Automation")
    if args.dry_run:
        logger.info("*** DRY RUN MODE — no DB writes ***")
    logger.info("=" * 60)

    try:
        # Step 1: Fetch recent conversations
        conversations = fetch_recent_conversations(args.days)

        if not conversations:
            logger.info("No conversations found for analysis")
            return 0

        # Step 2: Analyze with LLM Council
        raw_suggestions = analyze_with_council(conversations)

        if not raw_suggestions:
            logger.info("No suggestions generated")
            return 0

        raw_count = len(raw_suggestions)

        # Step 3: Cross-run dedup against existing suggestions + installed tooling
        existing_titles = fetch_existing_suggestions()
        installed_tools = fetch_installed_tooling()
        deduped, dedup_report = dedup_against_existing(
            raw_suggestions, existing_titles, installed_tools
        )

        # Step 4: Intake throttling
        to_insert, throttled = throttle_suggestions(deduped, args.max_suggestions)

        # Step 5: Insert surviving suggestions
        source_session = conversations[0]['session_id'] if conversations else None
        inserted = insert_suggestions(to_insert, source_session, dry_run=args.dry_run)

        # Step 6: Summary
        logger.info("=" * 60)
        logger.info("Daily Review Complete")
        logger.info(f"  Conversations analyzed:    {len(conversations)}")
        logger.info(f"  Suggestions from Council:  {raw_count}")
        logger.info(f"  Skipped (existing title):  {len(dedup_report['skipped_existing'])}")
        logger.info(f"  Skipped (installed tool):  {len(dedup_report['skipped_tooling'])}")
        logger.info(f"  Throttled (over cap {args.max_suggestions}):   {len(throttled)}")
        logger.info(f"  Actually inserted:         {inserted}")
        logger.info("=" * 60)

        return 0

    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())
