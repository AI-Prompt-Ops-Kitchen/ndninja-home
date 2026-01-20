from typing import Dict, Any, List, Optional
from datetime import datetime
import json
from tools_db.models import AuditTrailEvent


class AuditTrail:
    """Audit trail for tracking all changes"""

    def __init__(self, test_mode=False):
        self.test_mode = test_mode
        self.db = None
        if not test_mode:
            try:
                from tools_db.database import get_db
                self.db = get_db()
            except:
                pass
        self._memory_events = []  # For test_mode

    def record_event(
        self,
        event_type: str,
        entity_type: str,
        entity_id: str,
        old_value: Optional[Dict[str, Any]] = None,
        new_value: Optional[Dict[str, Any]] = None,
        user: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Record an audit event"""
        event = AuditTrailEvent(
            event_type=event_type,
            entity_type=entity_type,
            entity_id=entity_id,
            old_value=old_value,
            new_value=new_value,
            user=user,
            context=context
        )

        if self.test_mode:
            self._memory_events.append(event.to_dict())
            return True

        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO audit_trail_events
                    (event_type, entity_type, entity_id, old_value, new_value, user, context)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    event_type,
                    entity_type,
                    entity_id,
                    json.dumps(old_value) if old_value else None,
                    json.dumps(new_value) if new_value else None,
                    user,
                    json.dumps(context) if context else None
                ))
                return True
        except Exception as e:
            print(f"Audit record error: {e}")
            return False

    def get_events(
        self,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Retrieve audit events"""
        if self.test_mode:
            events = self._memory_events
            if entity_type:
                events = [e for e in events if e["entity_type"] == entity_type]
            if entity_id:
                events = [e for e in events if e["entity_id"] == entity_id]
            return events[:limit]

        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                query = "SELECT * FROM audit_trail_events WHERE 1=1"
                params = []

                if entity_type:
                    query += " AND entity_type = %s"
                    params.append(entity_type)
                if entity_id:
                    query += " AND entity_id = %s"
                    params.append(entity_id)
                if start_date:
                    query += " AND timestamp >= %s"
                    params.append(start_date)
                if end_date:
                    query += " AND timestamp <= %s"
                    params.append(end_date)

                query += " ORDER BY timestamp DESC LIMIT %s"
                params.append(limit)

                cursor.execute(query, params)
                columns = [desc[0] for desc in cursor.description]

                return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except Exception as e:
            print(f"Audit get error: {e}")
            return []

    def get_rollback_info(
        self,
        entity_type: str,
        entity_id: str,
        steps: int = 5
    ) -> List[Dict[str, Any]]:
        """Get rollback points for entity"""
        events = self.get_events(
            entity_type=entity_type,
            entity_id=entity_id,
            limit=steps
        )

        return [
            {
                "timestamp": e.get("timestamp"),
                "event_type": e.get("event_type"),
                "user": e.get("user"),
                "old_value": e.get("old_value"),
                "new_value": e.get("new_value")
            }
            for e in events
        ]

    def export_audit_log(
        self,
        entity_type: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        output_format: str = "json"
    ) -> str:
        """Export audit log in specified format"""
        events = self.get_events(
            entity_type=entity_type,
            start_date=start_date,
            end_date=end_date,
            limit=10000
        )

        if output_format == "json":
            return json.dumps(events, default=str, indent=2)
        elif output_format == "csv":
            # CSV export
            import csv
            from io import StringIO

            output = StringIO()
            if events:
                writer = csv.DictWriter(output, fieldnames=events[0].keys())
                writer.writeheader()
                writer.writerows(events)
            return output.getvalue()
        else:
            raise ValueError(f"Unsupported format: {output_format}")
