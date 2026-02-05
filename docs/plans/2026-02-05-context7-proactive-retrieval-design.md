# Context7 Proactive Retrieval System Design

**Date:** 2026-02-05
**Status:** Design Approved
**Priority:** High (from daily review suggestions)

## Overview

Implement intelligent, proactive documentation retrieval using Context7 MCP plugin with Redis+PostgreSQL caching to eliminate redundant API calls and provide instant access to frequently-used library documentation.

## Goals

1. **Proactive Loading**: Automatically preload docs for detected project libraries at session start
2. **Zero Latency**: Cache frequently-accessed docs for instant retrieval
3. **Smart Learning**: Track usage patterns to improve preload accuracy over time
4. **Cost Efficiency**: Deduplicate queries and cache aggressively to minimize API calls

## Architecture

### System Components

#### 1. Cache Layer (Two-Tier)

**Redis (Hot Cache)**
- Purpose: Lightning-fast lookups during active sessions
- TTL: Usage-based (frequently accessed docs refresh if >24h old)
- Keys: `context7:cache:{fingerprint}`, `context7:project:{path}:libs`
- Handles: Session-level deduplication

**PostgreSQL (Persistent Storage)**
- Purpose: Long-term storage with usage analytics
- Tables: `context7_cache`, `context7_project_libraries`, `context7_query_log`
- Handles: Cross-session learning, query history, usage stats

**Cache Strategy:**
1. Check Redis (fast path)
2. If miss, check PostgreSQL (warm path)
3. If miss, query Context7 API (cold path)
4. Store in both Redis + PostgreSQL

#### 2. Detection Layer

**Manifest Parsers:**
- `package.json` → Extract dependencies + devDependencies
- `Gemfile` → Extract gems
- `requirements.txt` / `pyproject.toml` → Extract Python packages
- `go.mod` → Extract Go modules
- `Cargo.toml` → Extract Rust crates

**Version Detection:**
- Extract major version from lockfiles when available
- Fall back to major version from manifest
- Default to latest if version not found

**Usage Tracker:**
- Records every Context7 query per project directory
- After 2+ uses of a library, auto-add to project's preload list
- Combines manifest + usage for intelligent preloading

#### 3. Integration Points

**SessionStart Hook (`on-session-start-context7.sh`)**
- Runs in background (non-blocking)
- Detects project libraries (manifest + usage history)
- Ranks by: manifest presence (weight: 2) + usage count (weight: 1)
- Preloads top 5 libraries
- Timeout: 10 seconds

**`/load-docs` Skill**
- Manual on-demand loading: `/load-docs rails hotwire react`
- Checks cache first, fetches on miss
- Updates usage stats automatically
- Timeout: 30 seconds

**Background Refresh**
- Triggered on cache access if doc is >24h old
- Non-blocking: Old doc stays available until refresh completes
- Exponential backoff on failures

#### 4. Fingerprinting System

**Cache Key Format:** `{library}-{major_version}:{intent}`

**Examples:**
- `rails-7:authentication`
- `react-18:hooks`
- `nextjs-14:routing`

**Intent Extraction:**
Simple keyword matching for v1:
- "How do I implement Rails authentication?" → `authentication`
- "Next.js dynamic routing guide" → `routing`
- "React useEffect hook examples" → `hooks`

**Deduplication Logic:**
- Similar queries map to same intent
- "Rails auth", "Rails authentication", "Rails login" → `authentication`
- ~70%+ cache hit rate expected

## Database Schema

### PostgreSQL

```sql
-- Main cache table
CREATE TABLE context7_cache (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    fingerprint VARCHAR(255) UNIQUE NOT NULL,
    library_id VARCHAR(255) NOT NULL,
    library_version VARCHAR(50) NOT NULL,
    query_intent VARCHAR(255) NOT NULL,
    content JSONB NOT NULL,
    citations JSONB,
    query_count INTEGER DEFAULT 1,
    last_accessed TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_context7_cache_fingerprint ON context7_cache(fingerprint);
CREATE INDEX idx_context7_cache_library ON context7_cache(library_id, library_version);
CREATE INDEX idx_context7_cache_accessed ON context7_cache(last_accessed DESC);

-- Project library tracking
CREATE TABLE context7_project_libraries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_path VARCHAR(500) NOT NULL,
    library_id VARCHAR(255) NOT NULL,
    library_version VARCHAR(50),
    detection_source VARCHAR(50),  -- 'manifest' or 'usage'
    usage_count INTEGER DEFAULT 0,
    last_used TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(project_path, library_id)
);

CREATE INDEX idx_context7_proj_libs_path ON context7_project_libraries(project_path);
CREATE INDEX idx_context7_proj_libs_used ON context7_project_libraries(last_used DESC);

-- Query history for analytics
CREATE TABLE context7_query_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    fingerprint VARCHAR(255) NOT NULL,
    original_query TEXT,
    cache_hit BOOLEAN,
    response_time_ms INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_context7_log_created ON context7_query_log(created_at DESC);
CREATE INDEX idx_context7_log_hits ON context7_query_log(cache_hit);
```

### Redis Keys

```
context7:cache:{fingerprint} → JSONB doc content (TTL: usage-based)
context7:project:{project_path}:libs → SET of library IDs
```

## Implementation Components

### 1. SessionStart Hook

**File:** `~/.claude/hooks/on-session-start-context7.sh`

```bash
#!/bin/bash
# Context7 Proactive Preloader
# Runs in background, doesn't block session start

python3 ~/.claude/hooks/context7-preloader.py \
    --project-path "$PWD" \
    --max-preload 5 \
    --timeout 10 \
    >> ~/.logs/context7-preload.log 2>&1 &
```

### 2. Preloader Script

**File:** `~/.claude/hooks/context7-preloader.py`

**Logic:**
1. Parse manifest files in project root
2. Query PostgreSQL for usage-based libraries
3. Rank libraries: manifest (2 pts) + usage count (1 pt each)
4. Top 5 libraries → Check Redis
5. If missing/stale → Query Context7 MCP
6. Store in Redis + PostgreSQL
7. Update query_log with timing

**Timeout:** 10 seconds (graceful exit if exceeded)

### 3. `/load-docs` Skill

**File:** `~/.claude/skills/load-docs/skill.md`

**Usage:** `/load-docs rails hotwire react`

**Flow:**
1. Resolve library names to Context7 library IDs
2. Detect versions from project manifests
3. Generate fingerprints (major version + intent)
4. Check Redis → PostgreSQL → Context7 API
5. Update usage stats in `context7_project_libraries`
6. Output: "Loaded Rails 7, Hotwire 8, React 18 (2 from cache, 1 fetched - 850ms)"

### 4. Cache Refresh Logic

**File:** `~/.claude/hooks/lib/context7_cache.py`

**Refresh Criteria:**
- Doc accessed in last 24h AND doc age >24h → Refresh
- Rarely accessed docs expire naturally (no refresh)

**Implementation:**
- Non-blocking: Old doc remains available during refresh
- Background thread handles API call
- Atomic swap: Update cache only when new content ready

## Error Handling

### Graceful Degradation

| Failure | Behavior |
|---------|----------|
| Context7 API down | Use stale cache, log warning, retry in 5min |
| Redis unavailable | Skip Redis, use PostgreSQL only (slower) |
| PostgreSQL down | Use Redis only (lose persistence) |
| Manifest parse error | Fall back to usage-based detection |

### Rate Limiting

- Max 10 Context7 queries per SessionStart
- Max 3 simultaneous API calls
- Exponential backoff: 1s, 2s, 4s, 8s, stop

### Timeouts

- SessionStart preload: 10 seconds
- `/load-docs` skill: 30 seconds
- Background refresh: 60 seconds

### Cache Invalidation

- `/refresh-docs --force <library>` - Manual cache bust
- Automatic: Context7 returns different content hash

## Monitoring & Analytics

### Log Files

- `~/.logs/context7-preload.log` - SessionStart activity
- `~/.logs/context7-skill.log` - `/load-docs` usage
- `~/.logs/context7-cache.log` - Cache operations

### Analytics Queries

```sql
-- Daily cache performance
SELECT
    DATE(created_at) as date,
    COUNT(*) as total_queries,
    SUM(CASE WHEN cache_hit THEN 1 ELSE 0 END) as hits,
    ROUND(100.0 * SUM(CASE WHEN cache_hit THEN 1 ELSE 0 END) / COUNT(*), 2) as hit_rate,
    AVG(response_time_ms) as avg_response_time
FROM context7_query_log
WHERE created_at > NOW() - INTERVAL '7 days'
GROUP BY DATE(created_at)
ORDER BY date DESC;

-- Most queried libraries
SELECT
    library_id,
    library_version,
    query_count,
    last_accessed
FROM context7_cache
ORDER BY query_count DESC
LIMIT 10;

-- Project library learning
SELECT
    project_path,
    COUNT(*) as library_count,
    SUM(CASE WHEN detection_source='usage' THEN 1 ELSE 0 END) as learned,
    SUM(CASE WHEN detection_source='manifest' THEN 1 ELSE 0 END) as detected
FROM context7_project_libraries
GROUP BY project_path
ORDER BY library_count DESC;
```

### Health Check Skill

**Command:** `/check-context7`

**Output:**
```
Context7 Proactive Retrieval Status
====================================
✓ Redis: Connected (http://100.77.248.9:6379)
✓ PostgreSQL: Connected (claude_memory)
✓ Context7 API: Healthy

Cache Performance (Last 7 Days):
  Total Queries: 342
  Cache Hits: 256 (74.9%)
  Avg Response Time: 127ms

Top 5 Libraries:
  1. rails-7 (87 queries)
  2. react-18 (54 queries)
  3. nextjs-14 (43 queries)
  4. hotwire-8 (31 queries)
  5. typescript-5 (27 queries)

Current Project (/home/ndninja):
  Detected Libraries: 8
  From Manifest: 6
  From Usage: 2
```

## Performance Targets

- SessionStart preload: < 5 seconds (background)
- `/load-docs` cache hit: < 100ms
- `/load-docs` API fetch: < 3 seconds
- Cache hit rate: > 70% (after 2 weeks usage)
- Context7 API calls: < 20/day (typical use)

## Implementation Phases

### Phase 1: Foundation
1. Create PostgreSQL schema
2. Implement Redis connection handler
3. Build manifest parsers (npm, gem, pip)
4. Create fingerprinting logic

### Phase 2: Core Features
5. Build cache layer (Redis + PostgreSQL)
6. Implement SessionStart preloader
7. Create `/load-docs` skill
8. Add usage tracking

### Phase 3: Intelligence
9. Implement background refresh
10. Add usage-based learning
11. Build analytics queries
12. Create `/check-context7` health check

### Phase 4: Polish
13. Add error handling & retries
14. Implement rate limiting
15. Create monitoring dashboards
16. Write user documentation

## Success Criteria

1. **Functionality**: Preloads correct libraries for 90%+ of projects
2. **Performance**: SessionStart adds <2s perceived latency
3. **Efficiency**: 70%+ cache hit rate after 2 weeks
4. **Reliability**: Gracefully degrades when services unavailable
5. **Intelligence**: Auto-learns new libraries after 2 uses

## Dependencies

- Context7 MCP plugin (already installed)
- Redis server (already running, needs auth config)
- PostgreSQL `claude_memory` database
- Python packages: `redis`, `psycopg2`, `pyyaml`, `toml`

## Redis Configuration

```bash
# Get Redis password from config or create one
# Update ~/.claude/hooks/lib/context7_cache.py with credentials
REDIS_HOST=100.77.248.9
REDIS_PORT=6379
REDIS_PASSWORD=<from redis config>
REDIS_DB=2  # Use separate DB for Context7
```

## Open Questions

None - design validated and ready for implementation.

## Next Steps

1. Set up Redis auth and connection testing
2. Create PostgreSQL schema
3. Build manifest parser utilities
4. Implement Phase 1 components
