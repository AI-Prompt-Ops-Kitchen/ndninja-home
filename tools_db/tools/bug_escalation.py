from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import json
from tools_db.models import BugEscalation as BugEscalationModel


class BugEscalation:
    """Bug escalation and priority management"""

    # Priority rules
    CRITICAL_KEYWORDS = {
        "CriticalBugError", "SecurityVulnerability", "DataLoss",
        "ProjectCancellation", "OutputFormatError"
    }

    HIGH_IMPACT_KEYWORDS = {
        "DatabaseError", "AuthenticationError", "APIError",
        "PerformanceDegradation"
    }

    def __init__(self, test_mode=False):
        self.test_mode = test_mode
        self.db = None
        if not test_mode:
            try:
                from tools_db.database import get_db
                self.db = get_db()
            except:
                pass
        self._memory_bugs = {}  # For test_mode

    def report_bug(
        self,
        bug_id: str,
        error_type: str,
        error_message: str,
        stack_trace: Optional[str] = None,
        user_impact: str = "medium",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Report a bug for potential escalation"""
        priority = self.calculate_priority(
            error_type=error_type,
            user_impact=user_impact,
            frequency=1,
            deadline_hours=24
        )

        bug = BugEscalationModel(
            bug_id=bug_id,
            error_type=error_type,
            error_message=error_message,
            stack_trace=stack_trace,
            frequency=1,
            user_impact=user_impact,
            status="pending" if priority in ["high", "critical"] else "acknowledged",
            metadata=metadata or {"priority": priority}
        )

        if self.test_mode:
            self._memory_bugs[bug_id] = bug.__dict__
            return {"success": True, "bug_id": bug_id, "priority": priority}

        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO bug_escalations
                    (bug_id, error_type, error_message, stack_trace,
                     frequency, user_impact, status, metadata)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (bug_id) DO UPDATE SET
                    frequency = bug_escalations.frequency + 1,
                    status = CASE
                        WHEN bug_escalations.status = 'pending' THEN 'pending'
                        ELSE %s
                    END
                """, (
                    bug_id, error_type, error_message, stack_trace,
                    1, user_impact, "pending" if priority in ["high", "critical"] else "acknowledged",
                    json.dumps(metadata or {"priority": priority}),
                    "pending" if priority in ["high", "critical"] else "acknowledged"
                ))
                return {"success": True, "bug_id": bug_id, "priority": priority}
        except Exception as e:
            print(f"Bug report error: {e}")
            return {"success": False, "error": str(e)}

    def calculate_priority(
        self,
        error_type: str,
        user_impact: str,
        frequency: int = 1,
        deadline_hours: int = 24
    ) -> str:
        """Calculate bug priority based on multiple factors"""
        priority_score = 0

        # Error type scoring
        if error_type in self.CRITICAL_KEYWORDS:
            priority_score += 40
        elif error_type in self.HIGH_IMPACT_KEYWORDS:
            priority_score += 25
        else:
            priority_score += 10

        # User impact scoring
        impact_scores = {"low": 0, "medium": 15, "high": 30, "critical": 50}
        priority_score += impact_scores.get(user_impact, 15)

        # Frequency scoring
        priority_score += min(frequency * 5, 25)

        # Deadline scoring
        if deadline_hours < 4:
            priority_score += 40
        elif deadline_hours < 24:
            priority_score += 20

        # Convert score to priority level
        if priority_score >= 80:
            return "critical"
        elif priority_score >= 50:
            return "high"
        elif priority_score >= 30:
            return "medium"
        else:
            return "low"

    def get_escalations(
        self,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get escalated bugs"""
        if self.test_mode:
            bugs = list(self._memory_bugs.values())
            if status:
                bugs = [b for b in bugs if b.get("status") == status]
            if priority:
                bugs = [b for b in bugs if b.get("metadata", {}).get("priority") == priority]
            return bugs[:limit]

        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                query = "SELECT * FROM bug_escalations WHERE 1=1"
                params = []

                if status:
                    query += " AND status = %s"
                    params.append(status)

                query += " ORDER BY escalated_at DESC LIMIT %s"
                params.append(limit)

                cursor.execute(query, params)
                columns = [desc[0] for desc in cursor.description]

                return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except Exception as e:
            print(f"Get escalations error: {e}")
            return []

    def mark_resolved(
        self,
        bug_id: str,
        resolution: str,
        resolved_by: Optional[str] = None
    ) -> bool:
        """Mark bug as resolved"""
        if self.test_mode:
            if bug_id in self._memory_bugs:
                self._memory_bugs[bug_id]["status"] = "resolved"
                self._memory_bugs[bug_id]["resolved_at"] = datetime.now(timezone.utc)
                if "metadata" not in self._memory_bugs[bug_id]:
                    self._memory_bugs[bug_id]["metadata"] = {}
                self._memory_bugs[bug_id]["metadata"]["resolution"] = resolution
            return True

        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE bug_escalations
                    SET status = 'resolved', resolved_at = NOW(),
                        metadata = jsonb_set(metadata, '{resolution}', %s)
                    WHERE bug_id = %s
                """, (json.dumps(resolution), bug_id))
                return True
        except:
            return False

    def get_escalation_summary(self) -> Dict[str, Any]:
        """Get summary of escalations"""
        if self.test_mode:
            statuses = {}
            for bug in self._memory_bugs.values():
                status = bug.get("status", "unknown")
                statuses[status] = statuses.get(status, 0) + 1
            return {"by_status": statuses}

        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT status, COUNT(*) as count
                    FROM bug_escalations
                    GROUP BY status
                """)

                summary = {}
                for status, count in cursor.fetchall():
                    summary[status] = count

                return {"by_status": summary}
        except:
            return {}
