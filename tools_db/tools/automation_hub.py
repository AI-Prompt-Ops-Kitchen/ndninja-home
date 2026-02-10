from typing import Dict, Any, List, Optional
from tools_db.models import AutomationEvent
from tools_db.database import Database
from datetime import datetime, timezone
import json


class AutomationHub:
    """Central hub for automation events (production checks, action items, n8n failures)"""

    def __init__(self, db: Optional[Database] = None, test_mode: bool = False):
        self.test_mode = test_mode
        self.db = db
        if not db:
            from tools_db.database import get_db
            self.db = get_db()
        self._memory_events = []  # For test mode

    def store_event(self, event: AutomationEvent) -> int:
        """Store automation event to database"""
        if self.test_mode:
            self._memory_events.append(event)
            return len(self._memory_events)

        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO automation_events
                    (event_type, project_id, status, evidence, detected_from, metadata)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    event.event_type,
                    event.project_id,
                    event.status,
                    json.dumps(event.evidence),
                    event.detected_from,
                    json.dumps(event.metadata) if event.metadata else None
                ))
                return cursor.lastrowid
        except Exception as e:
            print(f"Error storing automation event: {e}")
            return None

    def get_project_status(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Get latest status for a project"""
        if self.test_mode:
            matching = [e for e in self._memory_events if e.project_id == project_id]
            if matching:
                latest = matching[-1]
                return {
                    "event_type": latest.event_type,
                    "status": latest.status,
                    "evidence": latest.evidence
                }
            return None

        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT event_type, status, evidence
                    FROM automation_events
                    WHERE project_id = ?
                    ORDER BY created_at DESC LIMIT 1
                """, (project_id,))

                row = cursor.fetchone()
                if row:
                    return {
                        "event_type": row[0],
                        "status": row[1],
                        "evidence": json.loads(row[2])
                    }
        except Exception as e:
            print(f"Error getting project status: {e}")

        return None

    def get_events_by_type(self, event_type: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get events by type"""
        if self.test_mode:
            matching = [e for e in self._memory_events if e.event_type == event_type]
            return [{
                "event_type": e.event_type,
                "project_id": e.project_id,
                "status": e.status,
                "evidence": e.evidence
            } for e in matching[:limit]]

        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT event_type, project_id, status, evidence
                    FROM automation_events
                    WHERE event_type = ?
                    ORDER BY created_at DESC
                    LIMIT ?
                """, (event_type, limit))

                results = []
                for row in cursor.fetchall():
                    results.append({
                        "event_type": row[0],
                        "project_id": row[1],
                        "status": row[2],
                        "evidence": json.loads(row[3])
                    })
                return results
        except Exception as e:
            print(f"Error getting events by type: {e}")
            return []
