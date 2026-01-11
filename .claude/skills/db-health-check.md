---
name: db-health-check
description: Quick database health check with prioritized recommendations
version: 2.0.0
category: database
args: ["[--detailed]", "[--table=TABLE_NAME]"]
when_to_use: "User wants to check workspace database health, find issues, or get next action recommendations. Run weekly or before major work sessions."
tags: [database, health-check, workspace, audhd-friendly]
last_reflection: 2026-01-11
reflection_count: 1
---
# Database Health Check

Quick health analysis of workspace database with prioritized, actionable recommendations.

**Consolidates:** Former `/db-audit` skill merged here for simplicity.

## Usage

```bash
/db-health-check              # Quick overview (default)
/db-health-check --detailed   # Full analysis with item-level details
/db-health-check --table=items  # Deep dive on specific table
```

## Quick Check (Default)

Run these 3 essential queries to get a health snapshot:

```sql
-- 1. Overview: counts by type and status
SELECT type, status, COUNT(*) as count
FROM items WHERE archived = false
GROUP BY type, status ORDER BY type, count DESC;

-- 2. Completion rates
SELECT type,
  COUNT(*) as total,
  COUNT(*) FILTER (WHERE status = 'completed') as done,
  ROUND(100.0 * COUNT(*) FILTER (WHERE status = 'completed') / COUNT(*), 1) as pct
FROM items WHERE type IN ('task', 'project') AND archived = false
GROUP BY type;

-- 3. Data quality issues
SELECT 'Missing body' as issue, COUNT(*) as count FROM items
WHERE (body IS NULL OR body = '') AND type IN ('task','project') AND archived = false
UNION ALL
SELECT 'Missing priority', COUNT(*) FROM items
WHERE priority IS NULL AND type IN ('task','project') AND status != 'completed' AND archived = false
UNION ALL
SELECT 'Orphan tasks', COUNT(*) FROM items
WHERE type = 'task' AND parent_id IS NULL AND archived = false;
```

## Output Format

```
🏥 Database Health - {date}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Items: X total (Y active)
Tasks: X% complete | Projects: Y% complete

⚠️ Issues Found:
  • Missing body: X items
  • Missing priority: X items
  • Orphan tasks: X items

🎯 Next Actions:
  1. [Highest priority fix]
  2. [Second priority]
  3. [Third priority]
```

## Detailed Mode (--detailed)

Add these queries for deeper analysis:

```sql
-- Stale items (no updates in 30+ days)
SELECT type, status, COUNT(*) as count,
  MIN(updated_at)::date as oldest
FROM items
WHERE updated_at < NOW() - INTERVAL '30 days'
  AND status IN ('in_progress', 'pending')
  AND archived = false
GROUP BY type, status;

-- Links/cross-references health
SELECT COUNT(*) as total_links FROM links;

-- Blocked items
SELECT title, created_at::date,
  EXTRACT(day FROM NOW() - created_at) as days_blocked
FROM items WHERE status = 'blocked' AND archived = false;

-- Suggestion pipeline
SELECT status, COUNT(*) FROM skill_suggestions GROUP BY status;
```

## Table-Specific Mode (--table=X)

Deep dive on single table: items, links, skill_suggestions, tags.

## Priority Levels

| Priority | Criteria | Action |
|----------|----------|--------|
| CRITICAL | Blocked items 30+ days, empty critical tables | Fix today |
| HIGH | Missing descriptions on active items, orphan tasks | Fix this week |
| MEDIUM | Stale items, missing categories | Fix this month |
| LOW | Optimization opportunities | When time permits |

## Implementation Notes

- Use `mcp__postgres-db__execute_sql` for all queries
- Run queries in parallel when possible
- Focus on actionable items, not just data dumps
- Include specific fix commands in recommendations

---

## 🧠 Learnings

### 2026-01-11 - Consolidation
**Signal:** "db-audit and db-health-check are redundant"
**What Changed:** Merged db-audit into this skill, simplified to essential queries
**Confidence:** High
**Source:** ralph-loop-suggestion-processing-2026-01-11
**Rationale:** Two overlapping skills caused confusion; one streamlined skill is better
