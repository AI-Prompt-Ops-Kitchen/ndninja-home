---
name: check-context7
description: Health check for the Context7 proactive retrieval system
version: 1.0.0
category: diagnostics
args: []
when_to_use: "User wants to check if Context7 caching infrastructure is healthy, see cache hit rates, or diagnose connection issues."
tags: [context7, health, diagnostics, caching]
---

# Check Context7

Run a health check on the Context7 proactive retrieval system. Reports connection status for Redis, PostgreSQL, and the Context7 MCP server, plus cache statistics.

## Usage

```bash
/check-context7
```

## Output

```
Context7 Health Check
=====================
Redis          OK  (127.0.0.1:6379 DB2, 12 keys)
PostgreSQL     OK  (claude_memory, 45 cached entries)
Context7 MCP   OK  (npx @upstash/context7-mcp)

Cache Stats (7 days)
  Hit rate:    78% (156/200 queries)
  Entries:     45
  Top libs:    fastapi-0, react-18, rails-7, nextjs-14, django-5

Project Libraries (detected)
  fastapi 0, uvicorn latest, asyncpg 0
```

## Implementation

When this skill is invoked, execute:

```bash
python3 ~/.claude/skills/check-context7/check_context7.py
```

Parse the output and present results to the user.
