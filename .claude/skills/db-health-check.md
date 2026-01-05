---
name: db-health-check
description: Run comprehensive health checks on workspace PostgreSQL database
version: 1.0.2
category: database
tags: [database, analysis, health-check, workspace]
last_reflection: 2026-01-05 07:21:01
reflection_count: 2
---
# Workspace Database Health Check

Run a comprehensive health analysis of the workspace PostgreSQL database to identify growth opportunities, data quality issues, and maintenance needs.

## Your Task

Execute the following health checks and provide a prioritized report with actionable recommendations:

### 1. Item Counts by Type and Status

Query item distribution across types (task, project, knowledge, toolkit, doc, note) and statuses (pending, in_progress, completed, archived).

```sql
SELECT
  type,
  status,
  COUNT(*) as count
FROM items
WHERE archived = false
GROUP BY type, status
ORDER BY type, count DESC;
```

Also get overall totals:
```sql
SELECT
  COUNT(*) as total_items,
  COUNT(*) FILTER (WHERE archived = true) as archived_count,
  COUNT(*) FILTER (WHERE archived = false) as active_count
FROM items;
```

### 2. Completion Rate Analysis

Calculate completion rates for tasks and projects to understand productivity patterns.

```sql
SELECT
  type,
  COUNT(*) as total,
  COUNT(*) FILTER (WHERE status = 'completed') as completed,
  ROUND(100.0 * COUNT(*) FILTER (WHERE status = 'completed') / COUNT(*), 1) as completion_rate_pct
FROM items
WHERE type IN ('task', 'project')
  AND archived = false
GROUP BY type;
```

### 3. Missing/NULL Field Analysis

Identify items with missing critical metadata, especially effectiveness ratings for toolkits.

```sql
-- Toolkits without effectiveness ratings
SELECT COUNT(*) as unrated_toolkits
FROM items
WHERE type = 'toolkit'
  AND category = 'Prompting'
  AND archived = false
  AND (metadata->>'effectiveness_rating') IS NULL;

-- Items without titles (data quality issue)
SELECT COUNT(*) as items_without_titles
FROM items
WHERE title IS NULL OR title = '';

-- Items without body content
SELECT type, COUNT(*) as empty_body_count
FROM items
WHERE (body IS NULL OR body = '')
  AND archived = false
GROUP BY type;
```

### 4. Cross-Reference (Links) Analysis

Check the knowledge graph connectivity.

```sql
-- Total links
SELECT COUNT(*) as total_links FROM links;

-- Links by type
SELECT
  link_type,
  COUNT(*) as count
FROM links
GROUP BY link_type
ORDER BY count DESC;

-- Items without any links (isolated nodes)
SELECT
  type,
  COUNT(*) as isolated_count
FROM items
WHERE archived = false
  AND id NOT IN (SELECT from_id FROM links UNION SELECT to_id FROM links)
GROUP BY type;
```

### 5. Parent-Child Relationship Analysis

Check for orphaned items and project structure health.

```sql
-- Items with invalid parent_id references
SELECT COUNT(*) as orphaned_items
FROM items i1
WHERE parent_id IS NOT NULL
  AND NOT EXISTS (
    SELECT 1 FROM items i2
    WHERE i2.id = i1.parent_id
  );

-- Project task distribution
SELECT
  p.title as project,
  COUNT(t.id) as task_count,
  COUNT(*) FILTER (WHERE t.status = 'completed') as completed_tasks,
  COUNT(*) FILTER (WHERE t.status = 'in_progress') as active_tasks,
  COUNT(*) FILTER (WHERE t.status = 'pending') as pending_tasks
FROM items p
LEFT JOIN items t ON t.parent_id = p.id AND t.type = 'task'
WHERE p.type = 'project'
  AND p.archived = false
GROUP BY p.id, p.title
ORDER BY task_count DESC;
```

### 6. Skill Suggestions Analysis

Check the daily review automation pipeline.

```sql
SELECT
  suggestion_type,
  priority,
  status,
  COUNT(*) as count
FROM skill_suggestions
GROUP BY suggestion_type, priority, status
ORDER BY
  CASE priority WHEN 'high' THEN 1 WHEN 'medium' THEN 2 WHEN 'low' THEN 3 END,
  suggestion_type;
```

## Output Format

Present findings in this structure:

### 🏥 Database Health Summary
- Total items: X (Y active, Z archived)
- Completion rate: X% tasks, Y% projects
- Links: X total cross-references
- Latest suggestions: X pending improvements

### ⚠️ Data Quality Issues
(List any issues found with counts)

### 📊 Growth Opportunities
(Prioritize based on impact)

### 🎯 Recommended Next Actions
1. [Highest priority action based on findings]
2. [Second priority]
3. [Third priority]

Include specific SQL commands for fixes where applicable (e.g., "UPDATE items SET..." or "Run /rate-toolkits for 33 unrated items").

## Implementation Notes

- Use the `mcp__postgres-db__execute_sql` tool for all queries
- Run queries in parallel where possible for efficiency
- Focus on actionable insights, not just raw data
- Prioritize findings by impact (empty critical tables > missing optional metadata)
- Reference specific item counts and percentages in recommendations

---

## 🧠 Learnings (Auto-Updated)

### 2026-01-05 07:21 - Preference
**Signal:** "Used .pgpass for secure PostgreSQL connections"
**What Changed:** Use .pgpass file for secure PostgreSQL authentication
**Confidence:** Medium
**Source:** 2025-12-31-year-end-accomplishments
**Rationale:** Security best practice for PostgreSQL connections that complements the sudo approach

### 2026-01-05 07:21 - Preference
**Signal:** "Used sudo -u postgres psql for database access instead of password authentication"
**What Changed:** Prefer sudo-based postgres access over password authentication
**Confidence:** Medium
**Source:** prompting-techniques-import-2026-01-03
**Rationale:** This is a security best practice that should be reflected in database-related skills
