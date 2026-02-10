---
name: db-audit
description: Comprehensive workspace database health check and actionable recommendations
version: 1.0.1
category: productivity
args: ["[--detailed]", "[--table=TABLE_NAME]"]
when_to_use: "User wants to check workspace database health, find incomplete items, identify data quality issues, or get next action recommendations. Useful for weekly reviews, data cleanup, and progress tracking."
tags: [database, audit, health-check, productivity, data-quality, audhd-friendly]
examples: 
last_reflection: 2026-01-05 07:26:08
reflection_count: 1
---
# Database Audit & Health Check

**Purpose:** Audit the workspace database for completion rates, data quality issues, empty tables, and provide actionable next steps. Designed for quick weekly reviews and systematic database maintenance.

## Usage

```bash
/db-audit [--detailed] [--table=TABLE_NAME]
```

**Parameters:**
- `--detailed` (optional): Include detailed breakdowns and item-level analysis
- `--table` (optional): Audit specific table only (items, links, skill_suggestions, etc.)

**Examples:**
```bash
/db-audit                           # Quick overview
/db-audit --detailed                # Full analysis with recommendations
/db-audit --table=items             # Audit items table only
/db-audit --table=skill_suggestions # Check suggestion pipeline
```

## Workflow

### Step 1: Database Connection & Schema Overview

Connect to workspace database and get schema information:

```sql
-- List all tables with row counts
SELECT
  schemaname,
  tablename,
  n_live_tup as row_count,
  n_dead_tup as dead_rows
FROM pg_stat_user_tables
WHERE schemaname = 'public'
ORDER BY n_live_tup DESC;
```

**Output format:**
```
📊 Workspace Database Overview
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Database: workspace
Tables: 4
Total rows: 247

Table breakdown:
  ├─ items: 189 rows
  ├─ skill_suggestions: 54 rows
  ├─ links: 0 rows (EMPTY)
  └─ metadata: 4 rows
```

### Step 2: Items Table Audit

**A. Completion Rates by Type**

```sql
SELECT
  type,
  status,
  COUNT(*) as count,
  ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (PARTITION BY type), 1) as pct
FROM items
WHERE archived = false
GROUP BY type, status
ORDER BY type,
  CASE status
    WHEN 'completed' THEN 1
    WHEN 'in_progress' THEN 2
    WHEN 'active' THEN 3
    WHEN 'pending' THEN 4
    WHEN 'planned' THEN 5
    WHEN 'blocked' THEN 6
    ELSE 7
  END;
```

**Output format:**
```
📈 Completion Rates by Type
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Projects (12 total):
  ✅ completed: 4 (33.3%)
  🔄 in_progress: 3 (25.0%)
  ⏸️  blocked: 2 (16.7%)
  ⏳ pending: 3 (25.0%)

Tasks (45 total):
  ✅ completed: 28 (62.2%)
  🔄 in_progress: 5 (11.1%)
  ⏳ pending: 10 (22.2%)
  🚫 blocked: 2 (4.4%)

Toolkits (8 total):
  ✅ completed: 6 (75.0%)
  🔄 in_progress: 1 (12.5%)
  ⏳ pending: 1 (12.5%)

Articles (3 total):
  ✅ completed: 1 (33.3%)
  📝 draft: 2 (66.7%)

Overall completion rate: 39/68 (57.4%)
```

**B. Data Quality Issues**

```sql
-- Find items with null or empty critical fields
SELECT
  'Missing title' as issue,
  COUNT(*) as count
FROM items
WHERE (title IS NULL OR title = '') AND archived = false
UNION ALL
SELECT
  'Missing body/description',
  COUNT(*)
FROM items
WHERE (body IS NULL OR body = '')
  AND type IN ('project', 'task', 'article')
  AND archived = false
UNION ALL
SELECT
  'Missing priority',
  COUNT(*)
FROM items
WHERE priority IS NULL
  AND type IN ('task', 'project')
  AND status IN ('pending', 'in_progress', 'active')
  AND archived = false
UNION ALL
SELECT
  'Missing category',
  COUNT(*)
FROM items
WHERE category IS NULL
  AND archived = false
UNION ALL
SELECT
  'Missing URL for resources',
  COUNT(*)
FROM items
WHERE type IN ('resource', 'article', 'link')
  AND (url IS NULL OR url = '')
  AND archived = false;
```

**Output format:**
```
⚠️  Data Quality Issues
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ✗ Missing title: 0 items
  ✗ Missing body/description: 12 items
  ✗ Missing priority: 8 items (tasks/projects)
  ✗ Missing category: 15 items
  ✗ Missing URL for resources: 2 items

Total issues: 37 items need attention
```

**C. Stale Items (No Recent Updates)**

```sql
SELECT
  type,
  status,
  COUNT(*) as count,
  MIN(updated_at) as oldest_update
FROM items
WHERE updated_at < NOW() - INTERVAL '30 days'
  AND status IN ('in_progress', 'pending', 'active')
  AND archived = false
GROUP BY type, status
ORDER BY MIN(updated_at);
```

**Output format:**
```
⏰ Stale Items (no updates in 30+ days)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  🔄 Tasks in_progress: 2 items (oldest: 2025-11-15)
  ⏳ Projects pending: 1 item (oldest: 2025-10-22)
  ⏳ Tasks pending: 5 items (oldest: 2025-11-08)

Recommendation: Review these for archival or status update
```

**D. Blocked Items Analysis**

```sql
SELECT
  id,
  type,
  title,
  body as blocker_reason,
  created_at,
  EXTRACT(day FROM NOW() - created_at) as days_blocked
FROM items
WHERE status = 'blocked'
  AND archived = false
ORDER BY created_at;
```

**Output format:**
```
🚫 Blocked Items (2 total)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. [PROJECT] Database Migration
   Blocked: "Waiting for API access credentials"
   Duration: 45 days

2. [TASK] Implement SSO
   Blocked: "Needs security audit approval"
   Duration: 12 days

Recommendation: Follow up on blockers or defer these items
```

### Step 3: Links Table Audit

```sql
-- Check link table population
SELECT
  COUNT(*) as total_links,
  COUNT(DISTINCT source_id) as items_with_outgoing_links,
  COUNT(DISTINCT target_id) as items_with_incoming_links,
  COUNT(CASE WHEN link_type = 'references' THEN 1 END) as reference_links,
  COUNT(CASE WHEN link_type = 'depends_on' THEN 1 END) as dependency_links,
  COUNT(CASE WHEN link_type = 'related_to' THEN 1 END) as related_links
FROM links;

-- If links table is empty
SELECT
  COUNT(*) as items_without_links
FROM items
WHERE id NOT IN (SELECT source_id FROM links UNION SELECT target_id FROM links)
  AND archived = false;
```

**Output format (if empty):**
```
🔗 Links & Relationships
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ⚠️  EMPTY TABLE: No cross-references created yet

  Impact:
    - 189 items have no relationships
    - Knowledge graph is unpopulated
    - Retrieval/reuse capability is limited

  Recommendation:
    → Create cross-references between related items
    → Link tasks to parent projects
    → Connect articles to referenced toolkits
    → Build dependency chains for complex projects
```

**Output format (if populated):**
```
🔗 Links & Relationships
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Total links: 47
  Items with outgoing links: 23
  Items with incoming links: 31

  Link types:
    ├─ references: 28 (59.6%)
    ├─ depends_on: 12 (25.5%)
    └─ related_to: 7 (14.9%)

  ✓ Graph connectivity established
```

### Step 4: Skill Suggestions Audit

```sql
SELECT
  status,
  suggestion_type,
  priority,
  COUNT(*) as count
FROM skill_suggestions
GROUP BY status, suggestion_type, priority
ORDER BY
  CASE status
    WHEN 'pending' THEN 1
    WHEN 'implemented' THEN 2
    WHEN 'dismissed' THEN 3
    WHEN 'deferred' THEN 4
  END,
  CASE priority
    WHEN 'high' THEN 1
    WHEN 'medium' THEN 2
    WHEN 'low' THEN 3
  END,
  suggestion_type;
```

**Output format:**
```
💡 Skill Suggestion Pipeline
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Pending (11 total):
  HIGH priority:
    ├─ Skills: 4 items
    ├─ Plugins: 4 items
    └─ Architecture: 2 items

  MEDIUM priority:
    ├─ Skills: 8 items
    └─ Optimizations: 3 items

Implemented (8 total):
  ├─ Skills: 3 (/verify-official, /blog-checklist, /daily-review)
  └─ Architecture: 5

Dismissed (5 total):
  └─ Duplicates/superseded items

Recommendation: Review pending HIGH priority items weekly
```

### Step 5: Orphaned Items Detection

```sql
-- Tasks without parent projects
SELECT
  id,
  title,
  status,
  priority,
  created_at
FROM items
WHERE type = 'task'
  AND (parent_id IS NULL OR parent_id NOT IN (SELECT id FROM items WHERE type = 'project'))
  AND archived = false
ORDER BY priority, created_at;
```

**Output format:**
```
🔍 Orphaned Items
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Tasks without parent project: 7 items

  HIGH priority:
    • "Set up CI/CD pipeline" (created 2025-12-10)
    • "Write API documentation" (created 2025-11-28)

  MEDIUM priority:
    • "Refactor authentication module" (created 2025-12-15)
    • "Add error logging" (created 2025-12-01)

  (3 more...)

Recommendation: Assign to projects or archive if no longer relevant
```

### Step 6: Progress Velocity Analysis

```sql
-- Completion velocity (last 30 days)
SELECT
  DATE(completed_at) as date,
  COUNT(*) as items_completed,
  STRING_AGG(type, ', ') as types
FROM items
WHERE completed_at >= NOW() - INTERVAL '30 days'
  AND status = 'completed'
GROUP BY DATE(completed_at)
ORDER BY date DESC
LIMIT 10;

-- Average time to completion
SELECT
  type,
  COUNT(*) as completed_count,
  ROUND(AVG(EXTRACT(epoch FROM (completed_at - created_at))/86400), 1) as avg_days_to_complete,
  MIN(EXTRACT(epoch FROM (completed_at - created_at))/86400) as min_days,
  MAX(EXTRACT(epoch FROM (completed_at - created_at))/86400) as max_days
FROM items
WHERE status = 'completed'
  AND completed_at >= NOW() - INTERVAL '90 days'
  AND created_at IS NOT NULL
  AND completed_at IS NOT NULL
GROUP BY type
HAVING COUNT(*) >= 3
ORDER BY completed_count DESC;
```

**Output format:**
```
📊 Progress Velocity (Last 30 Days)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Recent completions:
  2026-01-04: 3 items (task, task, project)
  2026-01-03: 5 items (task, task, skill, article, task)
  2026-01-02: 2 items (project, toolkit)
  2025-12-31: 1 item (task)

Total last 30 days: 28 items completed

Average time to completion (90-day window):
  ├─ Tasks: 5.2 days (min: 0.5, max: 45)
  ├─ Projects: 21.3 days (min: 7, max: 89)
  └─ Articles: 12.8 days (min: 3, max: 31)

Velocity trend: Stable (28 items/month)
```

### Step 7: Next Action Recommendations

Generate prioritized recommendations based on audit findings:

**Priority Matrix:**
1. **CRITICAL** - Blockers, empty critical tables, >50 stale items
2. **HIGH** - Data quality issues, orphaned high-priority items, suggestion backlog
3. **MEDIUM** - Missing metadata, link building, low-priority orphans
4. **LOW** - Optimization opportunities, archival candidates

**Output format:**
```
🎯 Recommended Next Actions
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔴 CRITICAL (do today):
  1. Review 2 blocked projects (blocked 45+ days)
     → Query: SELECT * FROM items WHERE status='blocked' ORDER BY created_at;

  2. Populate links table (knowledge graph empty)
     → Start with: Link tasks to parent projects
     → Command: /build-knowledge-graph (if skill exists)

🟠 HIGH PRIORITY (this week):
  3. Fix 12 items missing descriptions
     → Focus on: active tasks and in_progress projects
     → Query: SELECT id, title FROM items WHERE body IS NULL
              AND type IN ('task','project') AND status IN ('active','in_progress');

  4. Assign priorities to 8 active items
     → Needed for proper task activation workflow

  5. Implement 4 pending high-priority skills
     → Next: /activate-tasks, /db-audit, /track-action-items

🟡 MEDIUM PRIORITY (this month):
  6. Review 7 orphaned tasks
     → Assign to projects or archive

  7. Add categories to 15 uncategorized items
     → Improves filtering and organization

  8. Review 5 stale items (30+ days no update)
     → Archive or reactivate

🟢 LOW PRIORITY (when time permits):
  9. Build cross-references between related articles
  10. Archive old completed items (90+ days old)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Estimated time: 2-3 hours for CRITICAL + HIGH items
```

### Step 8: Generate Detailed Report (--detailed flag)

If `--detailed` flag is provided, include:

**Item-Level Listings:**
```sql
-- All items missing descriptions
SELECT
  id,
  type,
  title,
  status,
  priority,
  created_at
FROM items
WHERE (body IS NULL OR body = '')
  AND type IN ('project', 'task', 'article')
  AND archived = false
ORDER BY
  CASE priority
    WHEN 'high' THEN 1
    WHEN 'medium' THEN 2
    WHEN 'low' THEN 3
    ELSE 4
  END,
  created_at;
```

**Full Stale Item List:**
```sql
-- All stale items with details
SELECT
  id,
  type,
  title,
  status,
  priority,
  updated_at,
  EXTRACT(day FROM NOW() - updated_at) as days_stale
FROM items
WHERE updated_at < NOW() - INTERVAL '30 days'
  AND status IN ('in_progress', 'pending', 'active')
  AND archived = false
ORDER BY updated_at;
```

**Suggestion Implementation Progress:**
```sql
-- Detailed suggestion breakdown
SELECT
  id,
  title,
  suggestion_type,
  priority,
  status,
  created_at,
  implemented_at,
  CASE
    WHEN status = 'implemented'
    THEN EXTRACT(day FROM (implemented_at - created_at))
    ELSE EXTRACT(day FROM (NOW() - created_at))
  END as days_in_pipeline
FROM skill_suggestions
ORDER BY
  CASE status
    WHEN 'pending' THEN 1
    WHEN 'implemented' THEN 2
    WHEN 'dismissed' THEN 3
  END,
  CASE priority
    WHEN 'high' THEN 1
    WHEN 'medium' THEN 2
    WHEN 'low' THEN 3
  END,
  created_at DESC;
```

### Step 9: Table-Specific Audit (--table flag)

If `--table=TABLE_NAME` is specified, provide deep dive:

**For items table:**
- Full type breakdown with status distribution
- Priority distribution
- Category usage statistics
- Date range analysis (created, updated, completed)
- Text field length statistics (title, body)
- NULL field analysis by column

**For links table:**
- Link type distribution
- Most connected items (hub analysis)
- Bidirectional vs unidirectional links
- Orphaned items (no links)
- Broken links (references to deleted items)

**For skill_suggestions table:**
- Full listing with implementation notes
- Time in pipeline by priority
- Source session analysis
- Implementation rate by type

### Step 10: Save Audit Results (Optional)

**Record audit in workspace:**
```sql
INSERT INTO items (type, title, body, status, category)
VALUES (
  'audit',
  'Database Audit - {date}',
  '{audit_summary_markdown}',
  'completed',
  'system-maintenance'
);
```

**Export to Craft (if --save-to-craft flag):**
```bash
craft_mcp: create_document(
  title="Workspace Audit - {date}",
  content="{full_audit_report}",
  folder="Audits",
  tags=["audit", "database", "workspace", "health-check"]
)
```

## AuDHD-Friendly Features

**Reduces Overwhelm:**
- Clear priority levels (CRITICAL → HIGH → MEDIUM → LOW)
- Actionable recommendations with specific queries
- Time estimates ("2-3 hours for CRITICAL + HIGH")
- Visual hierarchy (emoji indicators, sections)

**Executive Function Support:**
- Automated detection (no manual hunting for issues)
- Pre-written queries (copy-paste to investigate)
- Next actions explicitly listed
- Can run repeatedly without thinking

**Progress Visibility:**
- Completion rates show momentum
- Velocity tracking shows productivity trends
- Recent completions celebrate progress
- Stale item detection prevents "forgotten tasks" anxiety

**Decision Fatigue Reduction:**
- Recommendations are prioritized automatically
- Clear "do this first" guidance
- Estimated time helps with planning
- Can delegate to future self ("this month" vs "when time permits")

## Integration with Other Skills

**Works well with:**
- `/activate-next-tasks` - Use audit to identify which project needs attention
- `/daily-review` - Audit findings inform suggestion generation
- `/track-action-items` - Convert audit recommendations to tracked items
- `/blog-checklist` - Audit can check for unpublished articles

**Workflow example:**
```bash
# 1. Run weekly audit
/db-audit --detailed

# 2. See that "Digital Content Creation" project has 5 pending tasks

# 3. Activate top 2 tasks
/activate-next-tasks "Digital Content Creation" 2

# 4. Work on tasks...

# 5. Run audit again to see progress
/db-audit
```

## Implementation Notes

### Database Access
- Use `mcp__postgres-db__execute_sql` tool for all queries
- Connect to workspace database (not claude_memory)
- Use read-only queries (no UPDATE/DELETE)
- Handle NULL values gracefully

### Performance Optimization
- Limit detailed queries to `--detailed` flag
- Use aggregations instead of full scans
- Cache common queries (if run multiple times)
- EXPLAIN ANALYZE for slow queries

### Visual Formatting
```python
# Emoji indicators
STATUS_EMOJI = {
    'completed': '✅',
    'in_progress': '🔄',
    'active': '🔄',
    'pending': '⏳',
    'blocked': '🚫',
    'planned': '📋',
    'draft': '📝'
}

PRIORITY_EMOJI = {
    'high': '🔴',
    'medium': '🟡',
    'low': '🟢'
}

# Table separators
HEADER = "━" * 60
SUBHEADER = "─" * 60
```

### Query Templates

Store reusable queries as constants:
```python
COMPLETION_RATE_QUERY = """
SELECT
  type,
  status,
  COUNT(*) as count,
  ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (PARTITION BY type), 1) as pct
FROM items
WHERE archived = false
GROUP BY type, status
ORDER BY type, status;
"""

DATA_QUALITY_QUERY = """
SELECT
  'Missing ' || column_name as issue,
  COUNT(*) as count
FROM items, LATERAL (
  VALUES
    ('title', title IS NULL OR title = ''),
    ('body', body IS NULL OR body = ''),
    ('priority', priority IS NULL),
    ('category', category IS NULL)
) AS checks(column_name, is_null)
WHERE is_null AND archived = false
GROUP BY column_name;
"""
```

## Success Criteria

A successful audit should:
1. ✅ Identify all data quality issues (nulls, empties, orphans)
2. ✅ Calculate accurate completion rates by type
3. ✅ Detect stale items (30+ days no update)
4. ✅ Analyze blocked items and blockers
5. ✅ Audit relationship/link health
6. ✅ Generate prioritized action recommendations
7. ✅ Complete in <30 seconds for quick mode
8. ✅ Provide specific SQL queries for investigation

**Measurement:** Audit reveals at least 3 actionable improvements per run, completion time <30s for standard mode.

## Example Output

```
📊 Workspace Database Audit - 2026-01-04 16:30
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Database: workspace
Tables: 4 | Total rows: 247

📈 Completion Rates
Projects: 4/12 completed (33.3%)
Tasks: 28/45 completed (62.2%)
Toolkits: 6/8 completed (75.0%)

⚠️  Data Quality Issues (37 total)
  ✗ Missing body: 12 items
  ✗ Missing priority: 8 items
  ✗ Missing category: 15 items
  ✗ Missing URL: 2 resources

🔗 Links & Relationships
  ⚠️  EMPTY: 189 items without connections
  → Knowledge graph unpopulated

💡 Skill Suggestions
  Pending HIGH: 4 skills, 4 plugins, 2 architecture
  Implemented: 8 items
  Pipeline health: Active

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎯 Recommended Next Actions

🔴 CRITICAL:
  1. Populate links table (knowledge graph empty)

🟠 HIGH PRIORITY:
  2. Fix 12 missing descriptions (tasks/projects)
  3. Assign priorities to 8 active items
  4. Implement 4 pending high-priority skills

Time estimate: 2-3 hours

Run '/db-audit --detailed' for full item-level breakdown
```

---

## 🧠 Learnings (Auto-Updated)

### 2026-01-05 07:26 - Preference
**Signal:** "Used sudo -u postgres psql for database access instead of password authentication"
**What Changed:** Preference for sudo-based PostgreSQL access over password authentication
**Confidence:** Medium
**Source:** prompting-techniques-import-2026-01-03
**Rationale:** This is a security and operational best practice for local PostgreSQL access that should be part of database auditing procedures
