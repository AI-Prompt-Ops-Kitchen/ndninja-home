---
name: load-docs
description: Manually load Context7 documentation for specified libraries with intelligent caching
version: 1.0.0
category: documentation
args: ["<library>", "[library...]", "[--refresh]", "[--version N]"]
when_to_use: "User wants to preload library documentation before writing code, or refresh cached docs for a specific library."
tags: [context7, documentation, caching, preload]
---

# Load Documentation

Load Context7 documentation for one or more libraries with intelligent two-tier caching (Redis + PostgreSQL).

## Usage

```bash
# Load docs for specific libraries
/load-docs rails hotwire react

# Specify a major version
/load-docs nextjs --version 14

# Force refresh from Context7 API (bypass cache)
/load-docs typescript --refresh

# Auto-detect from project manifests
/load-docs --auto
```

## Flags

- `--refresh` — Force re-fetch from Context7 API, bypassing cache
- `--version N` — Specify major version (default: auto-detect from manifest)
- `--auto` — Detect libraries from project manifest files (package.json, Gemfile, requirements.txt)

## How It Works

1. Resolves library names to Context7 library IDs
2. Detects versions from project manifest files (if not specified)
3. Generates cache fingerprint: `{library}-{version}:{intent}`
4. Checks cache: Redis (hot, 24h) → PostgreSQL (persistent)
5. On cache miss: fetches from Context7 MCP API
6. Updates usage statistics for smart preloading

## Output

```
Loading documentation...
  rails 7        cached (Redis)     15ms
  hotwire 8      cached (PostgreSQL) 42ms
  react 18       fetched (API)      1.2s

Loaded 3 libraries (2 cached, 1 fetched)
Total time: 1.26s
```

## Implementation

Run the load_docs.py script which orchestrates cache lookups and Context7 MCP queries.

### Your Task

When this skill is invoked, execute the following:

```bash
python3 ~/.claude/skills/load-docs/load_docs.py [arguments]
```

Parse the output and present results to the user. If Context7 MCP is not yet configured, inform the user and offer to help set it up.
