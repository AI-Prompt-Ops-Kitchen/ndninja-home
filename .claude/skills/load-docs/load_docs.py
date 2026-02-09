#!/usr/bin/env python3
"""
Load Context7 documentation with intelligent caching.

Usage: python3 load_docs.py <library> [<library>...] [--refresh] [--auto] [--version N]

Orchestrates cache lookups (Redis -> PostgreSQL) and Context7 MCP queries.
"""

import sys
import os
import time
import argparse
import logging
from pathlib import Path

# Add hooks lib to path (check worktree first, then main home)
_hooks_lib = os.path.join(os.path.dirname(__file__), '..', '..', 'hooks', 'lib')
if os.path.isdir(_hooks_lib):
    sys.path.insert(0, os.path.abspath(_hooks_lib))
else:
    sys.path.insert(0, os.path.expanduser('~/.claude/hooks/lib'))

from context7_cache import CacheManager
from context7_fingerprint import generate_fingerprint
from manifest_parsers import parse_all_manifests
from context7_mcp import Context7MCPClient

# Configure logging to file only (stdout is for user-facing output)
os.makedirs(os.path.expanduser('~/.logs'), exist_ok=True)
file_handler = logging.FileHandler(os.path.expanduser('~/.logs/context7-skill.log'))
file_handler.setFormatter(logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s'))
logger = logging.getLogger('load-docs')
logger.addHandler(file_handler)
logger.setLevel(logging.INFO)

# Redis password from /etc/redis/redis.conf
REDIS_PASSWORD = "8NsEZXThezZwCQe0nwjGMZErrWVLe666Yy4UMkFV6Z4="


def get_cache_manager():
    """Create cache manager with local connection details."""
    return CacheManager(
        redis_host="127.0.0.1",
        redis_port=6379,
        redis_db=2,
        redis_password=REDIS_PASSWORD,
        pg_config={
            'host': 'localhost',
            'database': 'claude_memory',
            'user': 'claude_mcp',
            'password': 'REDACTED'
        }
    )


def detect_libraries_from_project(project_path: str) -> list:
    """Auto-detect libraries from project manifest files."""
    libraries = parse_all_manifests(project_path)
    logger.info(f"Auto-detected {len(libraries)} libraries from {project_path}")
    return libraries


def load_library(cache_manager, library: str, version: str,
                 force_refresh: bool, mcp_client=None) -> dict:
    """Load documentation for a single library.

    Returns: {'library': str, 'version': str, 'source': str, 'time_ms': int, 'success': bool}
    """
    fingerprint = generate_fingerprint(library, version, "general")
    start = time.monotonic()

    result = {
        'library': library,
        'version': version,
        'source': 'miss',
        'time_ms': 0,
        'success': False
    }

    # Check cache (unless force refresh)
    if not force_refresh:
        cached = cache_manager.get(fingerprint)
        if cached:
            elapsed = int((time.monotonic() - start) * 1000)
            redis_key = f"context7:cache:{fingerprint}"
            if cache_manager.redis.get(redis_key):
                result['source'] = 'Redis'
            else:
                result['source'] = 'PostgreSQL'
            result['time_ms'] = elapsed
            result['success'] = True
            return result

    # Cache miss — fetch via Context7 MCP
    if mcp_client is None:
        elapsed = int((time.monotonic() - start) * 1000)
        result['time_ms'] = elapsed
        result['source'] = 'no_client'
        logger.warning(f"Cache MISS for {library}-{version} — no MCP client available")
        return result

    try:
        fetch_result = mcp_client.fetch_and_cache(
            library=library,
            version=version,
            intent='general',
            cache_manager=cache_manager
        )
        elapsed = int((time.monotonic() - start) * 1000)
        result['time_ms'] = elapsed
        if fetch_result['success']:
            result['source'] = 'API'
            result['success'] = True
        else:
            result['source'] = fetch_result['source']
    except Exception as e:
        elapsed = int((time.monotonic() - start) * 1000)
        result['time_ms'] = elapsed
        result['source'] = 'error'
        logger.error(f"MCP fetch failed for {library}-{version}: {e}")

    return result


def main():
    parser = argparse.ArgumentParser(description='Load Context7 documentation')
    parser.add_argument('libraries', nargs='*', help='Library names to load')
    parser.add_argument('--refresh', action='store_true', help='Force refresh from API')
    parser.add_argument('--auto', action='store_true', help='Auto-detect from project manifests')
    parser.add_argument('--version', type=str, default=None, help='Major version override')
    parser.add_argument('--project-path', type=str, default=os.getcwd(),
                        help='Project path for manifest detection')
    args = parser.parse_args()

    # Build library list
    lib_entries = []

    if args.auto:
        detected = detect_libraries_from_project(args.project_path)
        for lib in detected:
            lib_entries.append({
                'library': lib['library'],
                'version': lib['major_version']
            })

    for lib_name in (args.libraries or []):
        lib_entries.append({
            'library': lib_name,
            'version': args.version or 'latest'
        })

    if not lib_entries:
        print("Usage: /load-docs <library> [<library>...] [--refresh] [--auto]")
        print("       /load-docs --auto  (detect from project manifests)")
        return 1

    # Initialize cache and MCP client
    cache = get_cache_manager()
    mcp_client = None

    print(f"Loading documentation...")

    results = []
    cached_count = 0
    fetched_count = 0
    miss_count = 0

    for entry in lib_entries:
        result = load_library(cache, entry['library'], entry['version'],
                              args.refresh, mcp_client)
        # If cache miss and no MCP client yet, try connecting
        if not result['success'] and mcp_client is None:
            mcp_client = Context7MCPClient(timeout=30, max_queries=len(lib_entries) * 2)
            if mcp_client.connect():
                print("  Connected to Context7 MCP server")
                result = load_library(cache, entry['library'], entry['version'],
                                      args.refresh, mcp_client)
            else:
                print("  Could not connect to Context7 MCP server")
                mcp_client = None

        results.append(result)

        # Format output
        lib_label = f"{result['library']} {result['version']}"
        if result['success'] and result['source'] == 'API':
            fetched_count += 1
            print(f"  {lib_label:<20s} fetched (API)       {result['time_ms']}ms")
        elif result['success']:
            cached_count += 1
            print(f"  {lib_label:<20s} cached ({result['source']:<10s}) {result['time_ms']}ms")
        else:
            miss_count += 1
            print(f"  {lib_label:<20s} failed ({result['source']})")

    if mcp_client:
        mcp_client.close()

    # Summary
    print()
    total_ms = sum(r['time_ms'] for r in results)
    parts = []
    if cached_count:
        parts.append(f"{cached_count} cached")
    if fetched_count:
        parts.append(f"{fetched_count} fetched")
    if miss_count:
        parts.append(f"{miss_count} failed")
    summary = ', '.join(parts) if parts else 'none'
    print(f"Loaded {len(results)} libraries ({summary})")
    print(f"Total time: {total_ms}ms")

    return 0


if __name__ == '__main__':
    sys.exit(main())
