# Claude Memory DB — Deep Analysis Report

**Date:** 2026-01-26
**Analyst:** Clawd 🐾
**Subject:** Why preferences are forgotten while projects are remembered
**System:** claude-memory-db (PostgreSQL MCP server + SessionStart hook)

---

## 1. System Overview

### Architecture
The system has **three layers** of memory surfacing:

1. **SessionStart Hook** (`~/.claude/hooks/on-session-start-memory.sh`) — Runs at session start, has 5-second timeout, injects `additionalContext` into Claude's system prompt via `hookSpecificOutput`. Queries raw SQL against `claude_memory` database.

2. **MCP Server** (`server.py`) — FastMCP Python server with 31 tools across two databases (`claude_memory` + `workspace`). Provides on-demand read/write access to preferences, memories, projects, conversations, references, workspace items, and toolkits.

3. **Application Cache** (`SmartCache`) — In-memory TTL cache (120s–300s) reducing DB hits. Invalidated on writes.

### Data Flow (Session Startup)
```
Session starts
  → Hook fires (5s timeout)
    → 4 SQL queries via psql CLI:
        1. Infrastructure refs (Tailscale — LIMIT 3)
        2. Communication prefs (priority >= 10 — LIMIT 3)
        3. Active projects (LIMIT 3)
        4. Recent conversations (LIMIT 2)
    → Outputs JSON with additionalContext
  → Claude receives context in system prompt
  → MCP server available for on-demand queries (but NOT auto-called)
```

### The Critical Gap
The hook is the **only automatic preference delivery mechanism**. The MCP tools (`get_preferences`, `memory_read`) exist, but Claude must **choose** to call them. Without explicit instruction in the system prompt to do so, Claude has no reason to — it doesn't know what it doesn't know.

---

## 2. Root Cause Analysis — Why Preferences Are Forgotten

### ROOT CAUSE #1: The Hook's LIMIT 3 Silently Drops Preferences (CRITICAL)

The hook queries:
```sql
SELECT 'Preference', key, value
FROM preferences
WHERE preference_type = 'communication' AND priority >= 10
ORDER BY priority DESC
LIMIT 3;
```

There are **6 communication preferences** with priority >= 10. After the `always_use_tailscale_ip` (priority 100) takes slot 1, only **2 of the remaining 5** are surfaced. Which 2? PostgreSQL makes **no guarantee** about ordering of equal-priority rows — the result is **non-deterministic**. The "one question at a time" preference may or may not appear on any given session start.

**Impact:** 3 of 6 communication preferences are silently discarded every session. The user's most important AuDHD accommodations are subject to database row ordering luck.

### ROOT CAUSE #2: Only `communication` Type Preferences Are Loaded (CRITICAL)

The hook **hardcodes** `preference_type = 'communication'`. This means **17 of 23 active preferences** (74%) are completely invisible at session start:

| Type | Count | Hook Visible? |
|------|-------|---------------|
| communication | 6 | ✅ (but LIMIT 3 drops half) |
| tool | 8 | ❌ |
| coding | 4 | ❌ |
| technical | 2 | ❌ |
| work | 2 | ❌ |
| personal | 1 | ❌ |

The `database_preference` (priority 100!) — "ALWAYS use PostgreSQL" — is **never loaded by the hook** because it's `preference_type = 'technical'`.

### ROOT CAUSE #3: No MCP Auto-Invoke at Session Start

The MCP server has `get_preferences()` and `get_context_summary()` tools, but **Claude doesn't automatically call them**. The hook's `additionalContext` doesn't include an instruction like "Call `get_preferences()` to load all user preferences." Claude sees the 3 loaded preferences and assumes that's all there is.

### ROOT CAUSE #4: Duplicate Preference Entries Waste LIMIT Slots

Three preferences say essentially the same thing about asking one question at a time:

| Key | Value (abbreviated) |
|-----|---------------------|
| `question_format` | "Ask only ONE question at a time..." |
| `sequential_questions` | "Ask ONE question at a time..." |
| `one_question_at_a_time` | "Always ask ONE question at a time..." |

All have priority 10, same effective meaning. They compete for the same 3 LIMIT slots. If all 3 happen to be the ones selected, the user gets triple-coverage of one preference and zero coverage of `check_memory_before_questions` and `clarification_questions_policy`.

### ROOT CAUSE #5: Priority Granularity Is Insufficient

Only 3 distinct priority values exist: 0, 5, 10 (plus one at 100). With 16 preferences at priority 10, there's no way to differentiate between "critical AuDHD accommodation" and "nice-to-have tool preference." The priority system is essentially binary: important (≥10) or not.

### Why Projects ARE Remembered

Projects succeed because:
1. The hook loads **active projects** directly (with a reasonable LIMIT 3)
2. The workspace DB has only 28 active projects — small enough to fit
3. `get_session_context()` loads active projects from the workspace DB
4. Projects are large, named entities — Claude naturally references them
5. Projects exist in both `claude_memory.project_context` AND `workspace.items` — dual redundancy

Preferences fail because they're small, numerous, interchangeable-looking text blobs competing for 3 slots behind a type filter.

---

## 3. Performance Issues

### 3.1 Connection Pool: None
Every function call creates a new `psycopg2.connect()`. The `get_connection()` and `get_workspace_connection()` functions open and close connections per call. With 31 tools, a busy session could open 50+ connections.

**Fix:** Use `psycopg2.pool.ThreadedConnectionPool` or switch to `asyncpg` with connection pooling.

### 3.2 N+1 Query in `get_session_context()`
```python
for t in tasks:
    parent = get_parent(task_dict['id'])  # Each call opens a NEW connection
```
For 20 pending tasks, this makes **20 additional database connections + queries**. Should be a single JOIN.

### 3.3 N+1 Query in `get_project_with_tasks()`
Uses `get_children()` which opens its own connection, even though the function already has one open. Not as bad (single call), but still wasteful.

### 3.4 Missing Composite Index on Preferences
The hook queries `WHERE preference_type = 'communication' AND priority >= 10 ORDER BY priority DESC`. There's no composite index on `(preference_type, priority)`. Currently uses `idx_preferences_type` (single column) and then filters/sorts in memory. With 23 rows it doesn't matter, but it's architecturally sloppy.

### 3.5 Cache Key Collision Risk
The `SmartCache._make_key()` uses MD5 hashing, but the cache `get()` method checks **TTL against `self._default_ttl`** regardless of the TTL passed to `set()`. The `ttl` parameter in `set()` is accepted but **never stored or used**. All cache entries expire at the global 300s default, even if `set(key, value, ttl=600)` was called.

```python
def set(self, key: str, value: Any, ttl: int = None) -> None:
    self._cache[key] = value
    self._timestamps[key] = time.time()  # ttl parameter is IGNORED
```

### 3.6 search_all_memory Opens Up to 5 Separate Connections
Each context search opens a new connection. The `claude_memory` contexts (preferences, memories, conversations, references) could share one connection.

---

## 4. Bug Report

### BUG-001: Cache TTL Parameter Ignored (Severity: Medium)
**Location:** `SmartCache.set()` (line ~90)
**Issue:** The `ttl` parameter is accepted but never stored. `get()` always uses `self._default_ttl`.
**Impact:** `CACHE_CONFIG` with per-operation TTLs is cosmetic — all entries use 300s.
**Fix:** Store TTL per entry:
```python
def set(self, key, value, ttl=None):
    self._cache[key] = value
    self._timestamps[key] = time.time()
    self._ttls[key] = ttl or self._default_ttl

def get(self, key):
    if key in self._cache:
        ttl = self._ttls.get(key, self._default_ttl)
        if time.time() - self._timestamps[key] < ttl:
            ...
```

### BUG-002: Non-Deterministic Preference Selection (Severity: Critical)
**Location:** `on-session-start-memory.sh`, line 18
**Issue:** Equal-priority rows have no tiebreaker in `ORDER BY priority DESC`. PostgreSQL returns them in arbitrary order. Different sessions get different subsets of the LIMIT 3.
**Fix:** Add deterministic tiebreaker: `ORDER BY priority DESC, id ASC` or `ORDER BY priority DESC, key ASC`.

### BUG-003: Hook Output Truncated on Parse Failure (Severity: Medium)
**Location:** `on-session-start-memory.sh`, the heredoc
**Issue:** The `grep` + `cut` + `sed` pipeline will silently produce empty output if the SQL returns no rows for a category, resulting in partial/empty context sections.
**Impact:** If no infrastructure refs match, the "Critical Infrastructure" section is blank but still rendered.

### BUG-004: `invalidate_cache_for_write('preference')` Only Invalidates `context_summary` (Severity: Low)
**Location:** `invalidate_cache_for_write()`, invalidation_map
**Issue:** Writing a preference only invalidates `context_summary` cache. But `memory_read("preference")` results are NOT cached (no `@cached` decorator on `get_preferences`), so this is technically correct but misleading — the invalidation map implies preferences have their own cache category.

### BUG-005: `always_use_tailscale_ip` Misclassified (Severity: Medium)
**Location:** Database data
**Issue:** `always_use_tailscale_ip` has `preference_type = 'communication'` but it's an infrastructure/network preference. It's priority 100 and takes slot 1 of the 3 communication preference slots, pushing actual communication preferences out.
**Fix:** Reclassify to `preference_type = 'infrastructure'` or `'technical'` and load it separately.

### BUG-006: Three Duplicate "One Question" Preferences (Severity: Medium)
**Location:** Database data (IDs 11, 14, 19)
**Issue:** `question_format`, `sequential_questions`, and `one_question_at_a_time` all say "ask one question at a time." They compete for the same LIMIT 3 slots.
**Fix:** Consolidate into one preference with priority 100.

### BUG-007: `memory_write` Delete for Preferences Doesn't Log (Severity: Low)
**Location:** `memory_write()`, delete branch for type="preference"
**Issue:** The delete operation for preferences doesn't call `log_action()`, unlike memory and reference deletes. No audit trail.

### BUG-008: `search_all_memory` Workspace Query Assumes `search_vector` Column (Severity: Low)
**Location:** `search_all_memory()`, workspace search section
**Issue:** Uses `search_vector @@ plainto_tsquery(...)` but the schema.sql doesn't create a `search_vector` column or GIN index on the `items` table. This will fail silently or error if the column doesn't exist in the workspace DB.

---

## 5. Feature Proposals (Prioritized by Impact)

### P0 — CRITICAL: Fix the Hook to Load ALL Preferences

**Impact:** Immediate fix for the core complaint.

**Option A: Remove LIMIT, Load All Active Preferences**
```sql
SELECT 'Preference' as category, key, value
FROM preferences
WHERE active = true AND priority >= 5
ORDER BY priority DESC, preference_type, key;
```
With 23 preferences, the total text is ~4KB. Claude's context window is 200K tokens. This is negligible.

**Option B: Tiered Loading**
```sql
-- Critical (priority >= 50): Always load
SELECT key, value FROM preferences WHERE active = true AND priority >= 50;
-- Important (priority 10-49): Load top 10
SELECT key, value FROM preferences WHERE active = true AND priority BETWEEN 10 AND 49 ORDER BY priority DESC LIMIT 10;
-- Standard (priority < 10): Mention count, instruct to query
```

**Option C: Pre-compiled Preference Summary**
Create a materialized view or cached text blob that summarizes all preferences into a single compact paragraph, regenerated on preference writes.

**Recommendation:** Option A. 23 preferences × ~200 chars = ~4,600 chars = ~1,200 tokens. Trivial.

### P1 — HIGH: Deduplicate Preferences

Consolidate the three "one question" entries into a single high-priority preference:
```sql
-- Keep one, boost priority, enrich value
UPDATE preferences SET
    value = 'AuDHD accommodation: ALWAYS ask ONE question at a time. Wait for answer before asking the next. Never batch questions, even during planning. Multiple questions cause overwhelm and context-switching failures.',
    priority = 100
WHERE key = 'one_question_at_a_time';

-- Deactivate duplicates
UPDATE preferences SET active = false WHERE key IN ('question_format', 'sequential_questions');
```

### P2 — HIGH: Add Priority Tiers

Redesign priority scale:
| Priority | Tier | Description |
|----------|------|-------------|
| 100 | CRITICAL | Non-negotiable (AuDHD accommodations, Tailscale IP) |
| 75 | HIGH | Important behavioral rules (check memory first, no interruptions) |
| 50 | MEDIUM | Tool preferences (PostgreSQL, context7) |
| 25 | LOW | Nice-to-have (coding style, editor prefs) |
| 0 | DEFAULT | Informational only |

### P3 — HIGH: Add `system_prompt_include` Column to Preferences

```sql
ALTER TABLE preferences ADD COLUMN system_prompt_include BOOLEAN DEFAULT false;
```

Mark the 5-10 most critical preferences as `system_prompt_include = true`. The hook loads ONLY these. Everything else is available via MCP on-demand. This gives explicit control over what Claude sees at startup.

### P4 — MEDIUM: Connection Pooling

Replace `get_connection()` with a pool:
```python
from psycopg2.pool import ThreadedConnectionPool
pool = ThreadedConnectionPool(2, 10, **DB_CONFIG)

def get_connection():
    return pool.getconn()
```
With proper `pool.putconn()` in finally blocks.

### P5 — MEDIUM: Fix N+1 in `get_session_context()`

Replace the per-task parent lookup loop with a single query:
```sql
SELECT i.*, p.title as project_title
FROM items i
LEFT JOIN links l ON l.from_id = i.id AND l.link_type = 'child_of'
LEFT JOIN items p ON p.id = l.to_id AND p.type = 'project'
WHERE i.type = 'task'
  AND i.status IN ('pending', 'active', 'in_progress')
  AND i.archived = false
ORDER BY ...
```

### P6 — MEDIUM: Fix SmartCache TTL Bug

Store per-entry TTLs (see BUG-001 fix above).

### P7 — LOW: Add Preference Categories to Hook Context

The hook's `additionalContext` should list preference categories and counts, instructing Claude to query specific categories when relevant:
```
Preferences loaded: 5 critical (shown above)
Additional preferences available via MCP: 8 tool, 4 coding, 2 work
Use get_preferences(preference_type="tool") when starting technical work.
```

### P8 — LOW: Add GIN Index on Preferences Value for Full-Text Search

```sql
CREATE INDEX idx_preferences_value_gin ON preferences
USING gin(to_tsvector('english', value));
```

### P9 — LOW: Preference Inheritance / Context Matching

Allow preferences to be automatically filtered by detected context. If Claude is doing Rails work, auto-load `context_tag = 'rails_development'` preferences. Currently, context_tag exists in the schema but is never used for automatic filtering.

---

## 6. Architecture Recommendations

### 6.1 Separate "System Prompt Injection" from "On-Demand Memory"

The current architecture conflates two concerns:
1. **Always-present context** (preferences, accommodations, identity) → Should be in system prompt
2. **On-demand lookup** (project details, conversation history, references) → Should be MCP tools

**Recommendation:** Create a `session_context_template` table or a simple compiled text file that contains the "always load" preferences as a pre-rendered block. Regenerate it whenever preferences change. The hook reads one file instead of running 4 SQL queries.

### 6.2 Preference Versioning

Currently, preferences are updated in-place with only `memory_log` audit trail. Add a `version` column and keep history:
```sql
ALTER TABLE preferences ADD COLUMN version INTEGER DEFAULT 1;
-- On update: INSERT new row with version+1, soft-delete old
```

This enables "when did this preference change?" and rollback.

### 6.3 Preference Effectiveness Tracking

Add a feedback loop: when Claude violates a preference (e.g., asks multiple questions), log it. This creates data for:
- Identifying which preferences need stronger wording
- Measuring preference adherence over time
- Auto-boosting priority of frequently-violated preferences

### 6.4 Consider `CLAUDE.md` as Preference Delivery

Claude Code natively reads `CLAUDE.md` files at session start — no hook needed, no timeout risk, no SQL parsing. Critical preferences could be auto-generated into a `CLAUDE.md` section:

```markdown
## User Preferences (Auto-generated from claude_memory DB)
- ONE question at a time (AuDHD accommodation)
- ALWAYS use Tailscale IP 100.77.248.9, never localhost
- PostgreSQL for everything
- Check memory before asking questions
```

A cron job or hook regenerates this file when preferences change. This is **the most reliable delivery mechanism** because Claude Code reads it with zero chance of timeout, parse failure, or LIMIT truncation.

---

## 7. Immediate Action Plan

### Phase 1: Emergency Fix (30 minutes)
1. **Deduplicate** the three "one question" preferences → keep one at priority 100
2. **Reclassify** `always_use_tailscale_ip` from `communication` to `infrastructure`
3. **Remove LIMIT 3** from hook's preference query (or increase to LIMIT 20)
4. **Remove the `preference_type = 'communication'` filter** — load ALL high-priority prefs
5. **Add deterministic ordering**: `ORDER BY priority DESC, id ASC`

### Phase 2: Structural Fix (2 hours)
1. Add `system_prompt_include` column
2. Mark critical preferences
3. Rewrite hook to load all `system_prompt_include = true` preferences
4. Fix the SmartCache TTL bug
5. Fix N+1 in `get_session_context()`

### Phase 3: Architecture Upgrade (future sprint)
1. Auto-generate preferences section in `CLAUDE.md`
2. Add connection pooling
3. Implement preference versioning
4. Add priority tier system

---

## Summary

The preference forgetting problem is **not a database issue** — the data is there, correct, and well-indexed. It's a **delivery pipeline problem**:

1. The hook only loads `communication` preferences (missing 74% of preferences)
2. LIMIT 3 silently drops half of even the communication preferences
3. Non-deterministic ordering means which preferences survive is random
4. Three duplicate entries waste precious LIMIT slots
5. The Tailscale IP preference is miscategorized and steals a communication slot
6. No mechanism instructs Claude to proactively query remaining preferences via MCP

The fix is straightforward: load all high-priority preferences in the hook (they total ~4KB — negligible), deduplicate entries, and add a CLAUDE.md fallback for the most critical accommodations.

---

*First project together. Let's make it count.* 🐾⚔️
