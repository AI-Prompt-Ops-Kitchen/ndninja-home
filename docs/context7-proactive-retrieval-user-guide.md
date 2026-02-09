# Context7 Proactive Retrieval — User Guide

Automatically preloads library documentation at session start and caches it in a two-tier system (Redis + PostgreSQL) for instant access during development.

## Architecture

```
SessionStart hook
  └─ context7-preloader.py (background)
       ├─ Detect libraries from manifests (package.json, Gemfile, requirements.txt)
       ├─ Check cache: Redis (24h hot) → PostgreSQL (persistent)
       └─ On miss: Context7 MCP → cache result

/load-docs skill (interactive)
  └─ load_docs.py
       ├─ Same cache pipeline
       └─ Supports --refresh, --auto, --version

/check-context7 skill (diagnostics)
  └─ check_context7.py
       └─ Redis, PostgreSQL, MCP status + cache hit rate
```

## Prerequisites

- **Node.js / npx** — for `@upstash/context7-mcp`
- **Redis** — DB 2, password in `/etc/redis/redis.conf`
- **PostgreSQL** — `claude_memory` database with schema applied
- **Context7 plugin** — enabled in Claude Code settings

## Database Schema

Applied to `claude_memory` database (user `claude_mcp`):

- `context7_cache` — cached documentation (fingerprint, content, citations, query_count)
- `context7_project_libraries` — per-project usage tracking (library, version, usage_count)
- `context7_query_log` — analytics (fingerprint, cache_hit, response_time_ms)

## Skills

### `/load-docs`

Load documentation for specific libraries or auto-detect from project manifests.

```bash
# Specific libraries
/load-docs fastapi react

# With version override
/load-docs nextjs --version 14

# Force refresh (bypass cache)
/load-docs typescript --refresh

# Auto-detect from project manifests
/load-docs --auto
```

### `/check-context7`

Health check showing service status, cache hit rates, and detected libraries.

```bash
/check-context7
```

Output:

```
Context7 Health Check
========================================
  [+] Redis          OK  (127.0.0.1:6379 DB2, 12 keys)
  [+] PostgreSQL     OK  (claude_memory, 45 cached entries)
  [+] Context7 MCP   OK  (2 tools available)

Cache Stats (7 days)
  Hit rate:    78% (156/200 queries)
  Entries:     45
  Top libs:    fastapi-0, react-18, rails-7

Project Libraries (/path/to/project)
  fastapi 0, uvicorn latest, asyncpg 0
```

## SessionStart Preloading

The `on-session-start-context7.sh` hook runs `context7-preloader.py` in the background on every session start. It:

1. Parses manifest files in the current project directory
2. Queries `context7_project_libraries` for frequently-used libraries
3. Checks cache for each (Redis first, then PostgreSQL)
4. On cache miss, spawns the Context7 MCP server and fetches documentation
5. Stores results in both Redis (24h TTL) and PostgreSQL (persistent)
6. Tracks usage counts for smarter future preloading

Logs go to `~/.logs/context7-preload.log`.

## Cache Fingerprinting

Cache keys use the format `{library}-{major_version}:{intent}`, for example `fastapi-0:routing`. Intent is extracted from query keywords (authentication, routing, testing, etc.) or defaults to `general`.

## Troubleshooting

### Redis unavailable

The system degrades gracefully — PostgreSQL serves as the fallback cache tier. Redis is only the hot cache layer.

```bash
# Check Redis status
redis-cli -a "$(grep requirepass /etc/redis/redis.conf | awk '{print $2}')" ping
```

### PostgreSQL unavailable

Cache operations will fail but won't crash the session. Check the connection:

```bash
psql -h localhost -U claude_mcp -d claude_memory -c "SELECT 1;"
```

### Context7 MCP errors

The MCP server is spawned via `npx -y @upstash/context7-mcp`. Common issues:

- **npx not found**: Ensure Node.js is installed and on PATH
- **Network timeout**: The server needs internet access to fetch docs
- **Rate limiting**: The client enforces per-session query limits to prevent abuse

### Cache invalidation

To clear cached docs for a library:

```sql
-- Clear specific library from PostgreSQL
DELETE FROM context7_cache WHERE library_id LIKE '%fastapi%';

-- Clear all Redis cache keys
redis-cli -n 2 -a "$PASSWORD" KEYS "context7:cache:*" | xargs redis-cli -n 2 -a "$PASSWORD" DEL
```

## Configuration

Key files:

| File | Purpose |
|------|---------|
| `.claude/hooks/on-session-start-context7.sh` | SessionStart hook wrapper |
| `.claude/hooks/context7-preloader.py` | Background preloader |
| `.claude/hooks/lib/context7_mcp.py` | MCP client (JSON-RPC over stdio) |
| `.claude/hooks/lib/context7_cache.py` | Two-tier cache manager |
| `.claude/hooks/lib/context7_redis.py` | Redis client with graceful degradation |
| `.claude/hooks/lib/context7_fingerprint.py` | Cache key generation |
| `.claude/hooks/lib/manifest_parsers.py` | package.json / Gemfile / requirements.txt parsers |
| `.claude/skills/load-docs/` | Interactive /load-docs skill |
| `.claude/skills/check-context7/` | Health check skill |
