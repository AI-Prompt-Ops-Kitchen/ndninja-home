#!/usr/bin/env python3
"""
Context7 health check.

Reports status of Redis, PostgreSQL, Context7 MCP, cache hit rates, and
detected project libraries.
"""

import sys
import os
import time

# Add hooks lib to path (check worktree first, then main home)
_hooks_lib = os.path.join(os.path.dirname(__file__), '..', '..', 'hooks', 'lib')
if os.path.isdir(_hooks_lib):
    sys.path.insert(0, os.path.abspath(_hooks_lib))
else:
    sys.path.insert(0, os.path.expanduser('~/.claude/hooks/lib'))

REDIS_PASSWORD = "8NsEZXThezZwCQe0nwjGMZErrWVLe666Yy4UMkFV6Z4="


def check_redis():
    """Check Redis connectivity and key count."""
    try:
        from context7_redis import RedisClient
        client = RedisClient("127.0.0.1", 6379, 2, REDIS_PASSWORD)
        if not client.ping():
            return False, "ping failed"
        keys = client._client.keys("context7:cache:*")
        return True, f"127.0.0.1:6379 DB2, {len(keys)} keys"
    except Exception as e:
        return False, str(e)


def check_postgres():
    """Check PostgreSQL connectivity and entry count."""
    try:
        import psycopg2
        conn = psycopg2.connect(
            host='localhost', database='claude_memory',
            user='claude_mcp', password='REDACTED'
        )
        cur = conn.cursor()
        cur.execute("SELECT count(*) FROM context7_cache;")
        count = cur.fetchone()[0]
        conn.close()
        return True, f"claude_memory, {count} cached entries"
    except Exception as e:
        return False, str(e)


def check_mcp():
    """Check Context7 MCP server can start."""
    try:
        from context7_mcp import Context7MCPClient
        client = Context7MCPClient(timeout=15, max_queries=1)
        ok = client.connect()
        if ok:
            tools = client.discover_tools()
            client.close()
            return True, f"{len(tools)} tools available"
        client.close()
        return False, "connect failed"
    except Exception as e:
        return False, str(e)


def get_cache_stats():
    """Get cache hit rate from last 7 days."""
    try:
        import psycopg2
        from psycopg2.extras import RealDictCursor
        conn = psycopg2.connect(
            host='localhost', database='claude_memory',
            user='claude_mcp', password='REDACTED'
        )
        cur = conn.cursor(cursor_factory=RealDictCursor)

        # Hit rate
        cur.execute("""
            SELECT
                count(*) AS total,
                count(*) FILTER (WHERE cache_hit) AS hits
            FROM context7_query_log
            WHERE created_at >= NOW() - INTERVAL '7 days';
        """)
        row = cur.fetchone()
        total = row['total'] or 0
        hits = row['hits'] or 0

        # Total entries
        cur.execute("SELECT count(*) AS cnt FROM context7_cache;")
        entries = cur.fetchone()['cnt']

        # Top libraries
        cur.execute("""
            SELECT library_id, library_version, query_count
            FROM context7_cache
            ORDER BY query_count DESC
            LIMIT 5;
        """)
        top_libs = cur.fetchall()

        conn.close()
        return {
            'total': total, 'hits': hits, 'entries': entries,
            'top_libs': top_libs
        }
    except Exception as e:
        return {'error': str(e)}


def get_project_libraries(project_path):
    """Detect libraries from current project."""
    try:
        from manifest_parsers import parse_all_manifests
        return parse_all_manifests(project_path)
    except Exception:
        return []


def main():
    project_path = os.getcwd()

    print("Context7 Health Check")
    print("=" * 40)

    # Service checks
    for name, checker in [("Redis", check_redis), ("PostgreSQL", check_postgres),
                          ("Context7 MCP", check_mcp)]:
        ok, detail = checker()
        status = "OK" if ok else "FAIL"
        indicator = "+" if ok else "!"
        print(f"  [{indicator}] {name:<14s} {status}  ({detail})")

    # Cache stats
    print()
    stats = get_cache_stats()
    if 'error' in stats:
        print(f"Cache Stats: error ({stats['error']})")
    else:
        total = stats['total']
        hits = stats['hits']
        rate = f"{hits * 100 // total}%" if total > 0 else "N/A"
        rate_detail = f" ({hits}/{total} queries)" if total > 0 else ""
        print(f"Cache Stats (7 days)")
        print(f"  Hit rate:    {rate}{rate_detail}")
        print(f"  Entries:     {stats['entries']}")
        if stats['top_libs']:
            libs = ", ".join(
                f"{r['library_id']}-{r['library_version']}"
                for r in stats['top_libs']
            )
            print(f"  Top libs:    {libs}")

    # Project libraries
    print()
    libs = get_project_libraries(project_path)
    if libs:
        print(f"Project Libraries ({project_path})")
        lib_strs = ", ".join(f"{l['library']} {l['major_version']}" for l in libs[:10])
        print(f"  {lib_strs}")
    else:
        print(f"Project Libraries: none detected in {project_path}")

    return 0


if __name__ == '__main__':
    sys.exit(main())
