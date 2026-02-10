"""Database module for tools_db - handles SQLite database operations"""

import sqlite3
from contextlib import contextmanager
from typing import Optional, Generator
import os


class Database:
    """SQLite database connection and management"""

    def __init__(self, connection_string: str = "sqlite:///:memory:"):
        """Initialize database with connection string"""
        # Parse connection string
        if connection_string.startswith("sqlite:///"):
            self.db_path = connection_string.replace("sqlite:///", "")
            if self.db_path == ":memory:":
                self.db_path = ":memory:"
        else:
            self.db_path = connection_string

        self.connection_string = connection_string

        # For in-memory databases, keep a persistent connection
        self._persistent_conn = None
        if self.db_path == ":memory:":
            self._persistent_conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self._persistent_conn.row_factory = sqlite3.Row

        self._initialize_database()

    def _get_sqlite_connection(self) -> sqlite3.Connection:
        """Get SQLite connection"""
        # Use persistent connection for in-memory databases
        if self._persistent_conn is not None:
            return self._persistent_conn

        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    @contextmanager
    def get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        """Get a database connection as context manager"""
        conn = self._get_sqlite_connection()
        is_persistent = self._persistent_conn is not None and conn is self._persistent_conn

        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            # Don't close persistent connections
            if not is_persistent:
                conn.close()

    def _initialize_database(self):
        """Initialize database schema on first connection"""
        conn = self._get_sqlite_connection()
        is_persistent = self._persistent_conn is not None and conn is self._persistent_conn

        try:
            cursor = conn.cursor()

            # Create all tables
            sql = self._create_tables_sql()
            cursor.executescript(sql)
            conn.commit()
        finally:
            # Don't close persistent connections
            if not is_persistent:
                conn.close()

    def _create_tables_sql(self) -> str:
        """Return SQL to create all required tables"""
        return """
        -- Audit Trail Events table
        CREATE TABLE IF NOT EXISTS audit_trail_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_type TEXT NOT NULL,
            entity_type TEXT NOT NULL,
            entity_id TEXT NOT NULL,
            old_value TEXT,
            new_value TEXT,
            user TEXT,
            context TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX IF NOT EXISTS ix_audit_event_entity ON audit_trail_events(entity_type, entity_id);
        CREATE INDEX IF NOT EXISTS ix_audit_timestamp ON audit_trail_events(timestamp DESC);

        -- Vision Cache table
        CREATE TABLE IF NOT EXISTS vision_cache (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            image_hash TEXT UNIQUE NOT NULL,
            extracted_data TEXT NOT NULL,
            confidence_score REAL NOT NULL,
            model_version TEXT NOT NULL,
            image_url TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            expires_at DATETIME NOT NULL,
            hit_count INTEGER DEFAULT 0
        );

        CREATE INDEX IF NOT EXISTS ix_vision_hash ON vision_cache(image_hash);
        CREATE INDEX IF NOT EXISTS ix_vision_expires ON vision_cache(expires_at);

        -- Bug Escalation table
        CREATE TABLE IF NOT EXISTS bug_escalation (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bug_id TEXT UNIQUE NOT NULL,
            error_type TEXT NOT NULL,
            error_message TEXT NOT NULL,
            stack_trace TEXT,
            frequency INTEGER DEFAULT 1,
            user_impact TEXT DEFAULT 'medium',
            status TEXT DEFAULT 'pending',
            metadata TEXT,
            escalated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            resolved_at DATETIME
        );

        CREATE INDEX IF NOT EXISTS ix_bug_status ON bug_escalation(status);
        CREATE INDEX IF NOT EXISTS ix_bug_impact ON bug_escalation(user_impact);

        -- Prompt Versioning table
        CREATE TABLE IF NOT EXISTS prompt_versions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            prompt_id TEXT NOT NULL,
            version INTEGER NOT NULL,
            prompt_text TEXT NOT NULL,
            purpose TEXT NOT NULL,
            created_by TEXT,
            is_active BOOLEAN DEFAULT 0,
            test_results TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(prompt_id, version)
        );

        CREATE INDEX IF NOT EXISTS ix_prompt_id ON prompt_versions(prompt_id);
        CREATE INDEX IF NOT EXISTS ix_prompt_active ON prompt_versions(is_active, prompt_id);

        -- Automation Events table
        CREATE TABLE IF NOT EXISTS automation_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_type TEXT NOT NULL,
            project_id TEXT NOT NULL,
            status TEXT NOT NULL,
            evidence TEXT NOT NULL,
            detected_from TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            resolved_at DATETIME,
            metadata TEXT
        );

        CREATE INDEX IF NOT EXISTS ix_automation_event_type_project ON automation_events(event_type, project_id);
        CREATE INDEX IF NOT EXISTS ix_automation_created_at ON automation_events(created_at DESC);
        CREATE INDEX IF NOT EXISTS ix_automation_status ON automation_events(status);
        """


# Global database instance
_db_instance: Optional[Database] = None


def get_db(connection_string: str = "sqlite:///tools.db") -> Database:
    """Get or create global database instance"""
    global _db_instance
    if _db_instance is None:
        _db_instance = Database(connection_string)
    return _db_instance


def reset_db():
    """Reset database instance (useful for testing)"""
    global _db_instance
    _db_instance = None
