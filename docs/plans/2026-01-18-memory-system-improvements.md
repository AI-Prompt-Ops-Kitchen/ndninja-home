# Memory System Improvements Implementation Plan

**Date:** 2026-01-18
**Goal:** Improve memory system data organization, performance, and features
**Priorities:** 1) Data Organization, 2) Performance, 3) Features
**Total Effort:** 11-15 hours
**Project:** claude-memory-db MCP Server

## Context

The memory system is a dual-database MCP server:
- **claude_memory DB**: Session continuity (preferences, memories, conversations, projects, references)
- **workspace DB**: Unified data store (items, links, tags)

Current issues identified:
- Redundant relationship tracking (parent_id column + links table)
- Split brain architecture (projects in both DBs, disconnected)
- Unclear link semantics (7 link types, confusing)
- Missing cross-database queries
- No unified search across memory types

## Tasks

### Task 1: Unify Relationship Model (Phase 1)

**Goal:** Eliminate redundancy between parent_id column and links table for hierarchical relationships.

**Current State:**
- `items.parent_id` column: 44 items use it (all tasks → projects)
- `links` table: Has both `parent_of` (16) and `child_of` (38) link types
- Confusion about which is source of truth

**Requirements:**
1. Create migration script `migrations/001_unify_relationships.sql` that:
   - Creates `child_of` links for all existing parent_id relationships
   - Verifies migration with assertion (child_of count >= parent_id count)
   - Removes redundant `parent_of` links (inverse of child_of)
   - Backs up parent_id data to items.metadata JSONB
   - Includes commented-out DROP COLUMN statement (for manual execution after validation)

2. Add helper functions to `server.py` (around line 160):
   - `get_children(parent_id: str, child_type: str = None) -> list`
   - `get_parent(child_id: str) -> dict`

3. Update `get_project_with_tasks()` function (around line 950) to use new relationship model

**Test Requirements:**
- Run audit query to verify parent_id and links counts match
- Execute migration in transaction (should be rollbackable)
- Test get_project_with_tasks before and after migration
- Verify no broken references
- Check query performance

**Files to modify:**
- Create: `/home/ndninja/projects/claude-memory-db/migrations/001_unify_relationships.sql`
- Modify: `/home/ndninja/projects/claude-memory-db/server.py`

**Success Criteria:**
- Migration script runs without errors
- All parent_id relationships have corresponding child_of links
- Helper functions work correctly
- get_project_with_tasks returns same results as before
- No performance degradation

---

### Task 2: Bridge Split Brain Architecture (Phase 2)

**Goal:** Connect claude_memory entities to workspace items to enable cross-session continuity.

**Current State:**
- `project_context` table (claude_memory DB): 11 projects tracked
- `items` table type='project' (workspace DB): 15 projects
- No connection between conversation_summaries.action_items and workspace tasks
- No connection between project_context and workspace projects

**Requirements:**
1. Create migration script `migrations/002_workspace_bridge.sql` that:
   - Creates `workspace_links` table with columns:
     - id, local_table, local_id, workspace_item_id, link_type, metadata, created_at
   - Adds CHECK constraints for local_table and link_type values
   - Creates indexes on (local_table, local_id), (workspace_item_id), (link_type)
   - Adds UNIQUE constraint on (local_table, local_id, workspace_item_id, link_type)

2. Add bridge helper functions to `server.py` (around line 800):
   - `link_to_workspace(local_table, local_id, workspace_item_id, link_type, metadata) -> bool`
   - `get_workspace_links(local_table=None, local_id=None, workspace_item_id=None) -> list`

3. Update `save_conversation_summary()` (around line 430) to:
   - Auto-link spawned tasks when action_items contain 'workspace_task_id'
   - Call link_to_workspace with link_type='spawned_task'

4. Create new unified context tool:
   - `get_session_context(include_conversations=3, include_active_projects=True, include_pending_tasks=True)`
   - Combines recent conversations, active projects, pending tasks
   - Uses new relationship model (child_of links)
   - Add @cached decorator with 180s TTL

**Test Requirements:**
- Create test link using link_to_workspace
- Verify unique constraint prevents duplicates
- Test get_workspace_links filtering
- Test get_session_context returns expected structure

**Files to modify:**
- Create: `/home/ndninja/projects/claude-memory-db/migrations/002_workspace_bridge.sql`
- Modify: `/home/ndninja/projects/claude-memory-db/server.py`

**Success Criteria:**
- workspace_links table created successfully
- Bridge functions work correctly
- save_conversation_summary links tasks properly
- get_session_context provides unified view

---

### Task 3: Performance Optimizations (Phase 3)

**Goal:** Improve query performance with materialized views and expanded caching.

**Current State:**
- Smart caching only covers `get_context_summary()` and `get_workspace_items()`
- No caching for conversation lookups
- No materialized views for common aggregations

**Requirements:**
1. Create migration script `migrations/003_materialized_views.sql` (workspace DB) that:
   - Creates materialized view `project_summary` with:
     - Project details (id, title, status, priority, category, timestamps)
     - Aggregated task counts (total, completed, pending)
     - Completion percentage
     - Last task update timestamp
   - Creates indexes on id (unique), status, completion_percent
   - Creates `refresh_project_summary()` function

2. Expand caching in `server.py`:
   - Add CACHE_CONFIG dict around line 60 with TTLs
   - Add @cached decorator to `get_recent_conversations()` (300s TTL)
   - Add @cached decorator to `get_projects()` (300s TTL)
   - Add cache invalidation helper: `invalidate_cache_for_write(operation_type)`
   - Call invalidation in write operations (save_conversation_summary, etc.)

3. Add cache statistics tool:
   - `get_cache_stats() -> str` returning cache hit/miss stats

**Test Requirements:**
- Verify materialized view has correct data
- Test refresh_project_summary() function
- Verify caching works (hit rate > 0% after repeated queries)
- Check cache invalidation clears correct prefixes

**Files to modify:**
- Create: `/home/ndninja/projects/claude-memory-db/migrations/003_materialized_views.sql`
- Modify: `/home/ndninja/projects/claude-memory-db/server.py`

**Success Criteria:**
- Materialized view returns accurate project summaries
- Cached queries return in <1ms on cache hit
- Cache invalidation prevents stale data
- get_cache_stats shows cache performance

---

### Task 4: Unified Search (Phase 4)

**Goal:** Enable searching across all memory systems from a single tool.

**Current State:**
- Search fragmented: search_memories, search_workspace, no conversation search
- No way to search preferences or references by content
- Users must know which tool to use

**Requirements:**
1. Create new MCP tool in `server.py`:
   - `search_all_memory(query: str, contexts: list = None, limit: int = 20) -> str`
   - Searches across: preferences, memories, conversations, workspace, references
   - Uses ILIKE for simple searches, full-text search for workspace
   - Returns JSON with results grouped by context
   - Includes result counts per context

2. Implementation details:
   - Default contexts = all ['preferences', 'memories', 'conversations', 'workspace', 'references']
   - For workspace: use existing full-text index with ts_rank ordering
   - For conversations: search summary and topics_discussed JSONB
   - Include result summary with total_results and results_by_context counts

**Test Requirements:**
- Search for term that exists in multiple contexts
- Verify results include all contexts
- Test context filtering (only search specific contexts)
- Verify workspace uses full-text search ranking

**Files to modify:**
- Modify: `/home/ndninja/projects/claude-memory-db/server.py` (add around line 1700)

**Success Criteria:**
- Single tool searches all memory types
- Results properly grouped by context
- Full-text search works for workspace items
- Result counts are accurate

---

### Task 5: Testing & Documentation (Phase 5)

**Goal:** Validate all improvements and update documentation.

**Current State:**
- No test suite for new features
- ARCHITECTURE.md doesn't document new improvements

**Requirements:**
1. Create test suite `test_improvements.py` that tests:
   - `test_relationship_queries()`: get_children, get_parent
   - `test_workspace_bridge()`: link_to_workspace, get_workspace_links
   - `test_session_context()`: get_session_context structure
   - `test_unified_search()`: search_all_memory across contexts
   - `test_caching()`: cache stats and performance

2. Update documentation `ARCHITECTURE.md`:
   - Add section "Relationship Model" explaining unified child_of links
   - Add section "Workspace Bridge" documenting workspace_links table
   - Add section "Performance Optimizations" covering materialized views and caching
   - Add section "Unified Search" documenting search_all_memory tool
   - Update tool count and tool list

3. Run all tests and verify:
   - All migrations applied successfully
   - All tests pass
   - No regressions in existing functionality

**Test Requirements:**
- Run test suite with python test_improvements.py
- All 5 tests must pass
- Documentation is clear and accurate

**Files to modify:**
- Create: `/home/ndninja/projects/claude-memory-db/test_improvements.py`
- Modify: `/home/ndninja/projects/claude-memory-db/ARCHITECTURE.md`

**Success Criteria:**
- Test suite runs without errors
- All tests pass
- Documentation is complete and accurate
- No breaking changes to existing tools

---

## Task Dependencies

```
Task 1 (Unify Relationships)
    ↓
Task 2 (Bridge Split Brain) - depends on Task 1's relationship model
    ↓
Task 3 (Performance) - can use Task 2's bridge for optimizations
    ↓
Task 4 (Unified Search) - can leverage all previous improvements
    ↓
Task 5 (Testing & Docs) - validates everything
```

## Notes

- Each task should commit changes after completion
- Migrations should be run manually after review
- Testing should be done after each migration
- Cache should be monitored for performance improvements
- Rollback plan: Each migration is in a transaction and can be reverted

## Expected Outcomes

After completion:
- Single source of truth for relationships (links table)
- Cross-session continuity via workspace bridge
- 3x faster common queries via caching + materialized views
- Unified search across all memory types
- Comprehensive test coverage
- Updated documentation

## Database Locations

- claude_memory DB: localhost:5432/claude_memory
- workspace DB: localhost:5432/workspace
- Server code: /home/ndninja/projects/claude-memory-db/server.py
- Migrations: /home/ndninja/projects/claude-memory-db/migrations/
