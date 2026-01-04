"""Database adapter - queries workspace database"""
import psycopg2
from psycopg2.extras import RealDictCursor
from data_sources.base_adapter import BaseAdapter
from config import Config


class DbAdapter(BaseAdapter):
    """Adapter for querying workspace database"""

    def _get_connection(self):
        """Get database connection with fallback to read-only"""
        try:
            return psycopg2.connect(**Config.WORKSPACE_DB)
        except psycopg2.OperationalError:
            # Fall back to read-only credentials
            readonly_config = {
                'host': 'localhost',
                'port': 5432,
                'database': 'workspace',
                'user': 'mcp_reader',
                'password': 'mcp_read_only_2026'
            }
            return psycopg2.connect(**readonly_config)

    def gather(self, project, args):
        """
        Gather project data from workspace database

        Args:
            project: Project dict with id, title, body, etc.
            args: Command-line arguments

        Returns:
            dict: {'db': {tasks, related_docs, tasks_summary}}
        """
        data = {
            'project': project,
            'tasks': self._get_tasks(project['id']),
            'related_docs': self._get_related_docs(project['id']),
            'knowledge_items': self._get_knowledge_items(project['id'])
        }

        # Generate tasks summary
        tasks = data['tasks']
        data['tasks_summary'] = self._format_tasks_summary(tasks)

        return {'db': data}

    def _get_tasks(self, project_id):
        """Get all tasks for project"""
        conn = self._get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        cur.execute("""
            SELECT id, title, status, priority, body, created_at, completed_at
            FROM items
            WHERE type = 'task'
              AND parent_id = %s
              AND archived = false
            ORDER BY
                CASE priority
                    WHEN 'high' THEN 1
                    WHEN 'medium' THEN 2
                    WHEN 'low' THEN 3
                    ELSE 4
                END,
                created_at DESC
        """, (project_id,))

        result = cur.fetchall()
        conn.close()

        return [dict(r) for r in result]

    def _get_related_docs(self, project_id):
        """Get existing documentation for project"""
        conn = self._get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        cur.execute("""
            SELECT id, title, category, created_at, metadata
            FROM items
            WHERE type = 'doc'
              AND parent_id = %s
              AND archived = false
            ORDER BY created_at DESC
        """, (project_id,))

        result = cur.fetchall()
        conn.close()

        return [dict(r) for r in result]

    def _get_knowledge_items(self, project_id):
        """Get related knowledge items"""
        conn = self._get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        cur.execute("""
            SELECT k.id, k.title, k.body
            FROM items k
            JOIN links l ON (l.from_id = k.id OR l.to_id = k.id)
            WHERE k.type = 'knowledge'
              AND k.archived = false
              AND (l.from_id = %s OR l.to_id = %s)
            LIMIT 10
        """, (project_id, project_id))

        result = cur.fetchall()
        conn.close()

        return [dict(r) for r in result]

    def _format_tasks_summary(self, tasks):
        """Format tasks into readable summary"""
        total = len(tasks)
        completed = len([t for t in tasks if t['status'] == 'completed'])
        pending = len([t for t in tasks if t['status'] in ['pending', 'active']])
        high_priority = len([t for t in tasks if t['priority'] == 'high'])

        summary = f"""Total: {total}
Completed: {completed}
Pending: {pending}
High Priority: {high_priority}"""

        return summary
