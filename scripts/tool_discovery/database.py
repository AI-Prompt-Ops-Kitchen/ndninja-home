import psycopg2
import json
from typing import List, Dict, Optional

class ToolDatabase:
    """Database interface for tool registry in claude-memory"""

    def __init__(self):
        self.conn = None
        self.host = "localhost"
        self.user = "claude_mcp"
        self.database = "claude_memory"

    def connect(self) -> bool:
        """Connect to PostgreSQL database"""
        try:
            self.conn = psycopg2.connect(
                host=self.host,
                user=self.user,
                database=self.database,
                # Password from .pgpass
            )
            return True
        except Exception as e:
            print(f"Database connection failed: {e}")
            return False

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()

    def get_all_tools(self) -> List[Dict]:
        """Get all tools from registry"""
        if not self.conn:
            return []

        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT title, content, notes, updated_at
                FROM reference_info
                WHERE category = 'tool' AND active = true
                ORDER BY updated_at DESC
            """)

            tools = []
            for row in cursor.fetchall():
                title, content, notes, updated_at = row
                tool_data = json.loads(content) if isinstance(content, str) else content
                tools.append({
                    'key': title,
                    'data': tool_data,
                    'notes': notes,
                    'updated_at': updated_at
                })

            cursor.close()
            return tools
        except Exception as e:
            print(f"Error getting tools: {e}")
            return []
