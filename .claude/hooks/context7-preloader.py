#!/usr/bin/env python3
"""
Context7 session preloader.
Detects project libraries and preloads top N docs into cache.
Runs in background from SessionStart hook — must be fast and non-blocking.
"""

import sys
import os
import argparse
import logging
import time
from pathlib import Path

# Add lib to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'lib'))

from manifest_parsers import parse_all_manifests
from context7_cache import CacheManager
from context7_fingerprint import generate_fingerprint
from context7_mcp import Context7MCPClient

os.makedirs(os.path.expanduser('~/.logs'), exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler(os.path.expanduser('~/.logs/context7-preload.log')),
    ]
)
logger = logging.getLogger(__name__)

# Redis password
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


def get_top_libraries(project_path: str, max_count: int) -> list:
    """Get top N libraries to preload, combining manifest + usage data.

    Priority:
    1. Libraries from manifest files (current project)
    2. Libraries with highest usage_count from context7_project_libraries
    """
    libraries = []

    # Source 1: Manifest detection
    manifest_libs = parse_all_manifests(project_path)
    for lib in manifest_libs[:max_count]:
        libraries.append({
            'library': lib['library'],
            'version': lib['major_version'],
            'source': 'manifest'
        })

    if len(libraries) >= max_count:
        return libraries[:max_count]

    # Source 2: Usage-based from PostgreSQL (fill remaining slots)
    remaining = max_count - len(libraries)
    try:
        import psycopg2
        from psycopg2.extras import RealDictCursor

        conn = psycopg2.connect(
            host='localhost',
            database='claude_memory',
            user='claude_mcp',
            password='REDACTED'
        )
        cur = conn.cursor(cursor_factory=RealDictCursor)

        # Get most-used libraries for this project, excluding already-found ones
        manifest_names = {lib['library'] for lib in libraries}
        cur.execute("""
            SELECT library_id, library_version, usage_count
            FROM context7_project_libraries
            WHERE project_path = %s
            ORDER BY usage_count DESC, last_used DESC
            LIMIT %s;
        """, (project_path, remaining + len(manifest_names)))

        for row in cur.fetchall():
            if row['library_id'] not in manifest_names and len(libraries) < max_count:
                libraries.append({
                    'library': row['library_id'],
                    'version': row['library_version'] or 'latest',
                    'source': 'usage'
                })

        conn.close()
    except Exception as e:
        logger.warning(f"Could not query usage data: {e}")

    return libraries[:max_count]


def preload_libraries(cache_manager, libraries: list, timeout: int,
                      project_path: str = '') -> dict:
    """Preload libraries into cache via Context7 MCP.

    Returns: {'cached': int, 'fetched': int, 'missed': int, 'elapsed_ms': int}
    """
    start = time.monotonic()
    deadline = start + timeout
    stats = {'cached': 0, 'fetched': 0, 'missed': 0, 'elapsed_ms': 0}

    mcp_client = None

    for lib in libraries:
        if time.monotonic() > deadline:
            logger.warning(f"Preload timeout ({timeout}s) reached, stopping")
            break

        fingerprint = generate_fingerprint(lib['library'], lib['version'], 'general')
        cached = cache_manager.get(fingerprint)

        if cached:
            stats['cached'] += 1
            logger.info(f"  {lib['library']}-{lib['version']}: cached")
        else:
            # Lazy-connect MCP client on first cache miss
            if mcp_client is None:
                mcp_client = Context7MCPClient(
                    timeout=min(timeout, 30),
                    max_queries=len(libraries) * 2  # resolve + query per lib
                )
                if not mcp_client.connect():
                    logger.error("Could not connect to Context7 MCP server")
                    stats['missed'] += len(libraries) - stats['cached']
                    break

            try:
                result = mcp_client.fetch_and_cache(
                    library=lib['library'],
                    version=lib['version'],
                    intent='general',
                    cache_manager=cache_manager
                )
                if result['success']:
                    stats['fetched'] += 1
                    logger.info(f"  {lib['library']}-{lib['version']}: fetched ({result['time_ms']}ms)")
                else:
                    stats['missed'] += 1
                    logger.info(f"  {lib['library']}-{lib['version']}: {result['source']}")
            except Exception as e:
                stats['missed'] += 1
                logger.warning(f"  {lib['library']}-{lib['version']}: error ({e})")

        # Track usage regardless of cache hit or fetch
        if project_path:
            cache_manager.track_usage(
                project_path=project_path,
                library_id=lib['library'],
                library_version=lib['version'],
                detection_source=lib.get('source', 'manifest')
            )

    if mcp_client:
        mcp_client.close()

    stats['elapsed_ms'] = int((time.monotonic() - start) * 1000)
    return stats


def main():
    parser = argparse.ArgumentParser(description='Context7 session preloader')
    parser.add_argument('--project-path', required=True, help='Project directory')
    parser.add_argument('--max-preload', type=int, default=5, help='Max libraries to preload')
    parser.add_argument('--timeout', type=int, default=10, help='Timeout in seconds')
    args = parser.parse_args()

    logger.info("=" * 60)
    logger.info("Context7 SessionStart Preloader")
    logger.info(f"Project: {args.project_path}")

    # Detect libraries
    libraries = get_top_libraries(args.project_path, args.max_preload)
    logger.info(f"Detected {len(libraries)} libraries to preload")

    if not libraries:
        logger.info("No libraries detected, nothing to preload")
        logger.info("=" * 60)
        return 0

    for lib in libraries:
        logger.info(f"  {lib['library']} {lib['version']} ({lib['source']})")

    # Preload
    cache = get_cache_manager()
    stats = preload_libraries(cache, libraries, args.timeout, args.project_path)

    logger.info(f"Preload complete: {stats['cached']} cached, "
                f"{stats['fetched']} fetched, {stats['missed']} missed "
                f"({stats['elapsed_ms']}ms)")
    logger.info("=" * 60)

    return 0


if __name__ == '__main__':
    sys.exit(main())
