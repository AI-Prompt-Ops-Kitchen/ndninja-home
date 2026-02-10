"""Validation utilities for documentation generator"""
import psycopg2
from psycopg2.extras import RealDictCursor
from config import Config


def validate_project(project_name):
    """
    Validate and retrieve project from workspace database

    Args:
        project_name: Project title or partial match

    Returns:
        dict: Project record with id, title, body, metadata, status, category

    Raises:
        ValueError: If project not found or multiple matches
    """
    # Try main config first, fall back to read-only if needed
    try:
        conn = psycopg2.connect(**Config.WORKSPACE_DB)
    except psycopg2.OperationalError:
        # Fall back to read-only credentials
        readonly_config = {
            'host': 'localhost',
            'port': 5432,
            'database': 'workspace',
            'user': 'mcp_reader',
            'password': 'mcp_read_only_2026'
        }
        conn = psycopg2.connect(**readonly_config)

    cur = conn.cursor(cursor_factory=RealDictCursor)

    # Search for project by title (case-insensitive partial match)
    cur.execute("""
        SELECT id, title, body, status, category, metadata, created_at, updated_at
        FROM items
        WHERE type = 'project'
          AND archived = false
          AND title ILIKE %s
        ORDER BY
            CASE WHEN title ILIKE %s THEN 0 ELSE 1 END,  -- Exact match first
            updated_at DESC
    """, (f'%{project_name}%', project_name))

    results = cur.fetchall()
    conn.close()

    if not results:
        raise ValueError(f"No project found matching: {project_name}")

    if len(results) > 1:
        # Check for exact match
        exact_matches = [r for r in results if r['title'].lower() == project_name.lower()]
        if len(exact_matches) == 1:
            return dict(exact_matches[0])

        # Multiple matches, provide helpful error
        titles = [r['title'] for r in results[:5]]
        raise ValueError(
            f"Multiple projects found matching '{project_name}':\n" +
            "\n".join(f"  - {t}" for t in titles) +
            "\n\nPlease be more specific."
        )

    return dict(results[0])


def validate_api_key():
    """
    Validate that ANTHROPIC_API_KEY is set

    Raises:
        ValueError: If API key not found
    """
    if not Config.ANTHROPIC_API_KEY:
        raise ValueError(
            "ANTHROPIC_API_KEY environment variable not set.\n"
            "Please set it with: export ANTHROPIC_API_KEY='your-key-here'"
        )
