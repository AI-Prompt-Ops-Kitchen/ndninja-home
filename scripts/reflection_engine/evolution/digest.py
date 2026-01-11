"""
Weekly Evolution Digest Generator

Generates periodic summaries of skill evolution for review.
Can be triggered manually or via n8n automation.
"""

import psycopg2
from typing import Optional, Dict, List
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD, HOME_DIR

from .health import HealthCalculator
from .tracker import EventTracker
from .usage import UsageTracker


@dataclass
class DigestStats:
    """Statistics for a digest period"""
    period_start: datetime
    period_end: datetime
    reflections_applied: int
    skills_updated: int
    feedback_given: int
    skills_used: int
    health_improved: int
    health_declined: int
    attention_needed: int


class DigestGenerator:
    """Generates periodic evolution digests"""

    DIGEST_FILE = HOME_DIR / '.claude' / 'evolution-digest.md'
    ATTENTION_FILE = HOME_DIR / '.claude' / 'evolution-attention.md'

    def __init__(self, db_conn=None):
        self.db_conn = db_conn
        self._owns_connection = False
        self.health_calc = None
        self.tracker = None
        self.usage_tracker = None

    def connect(self):
        """Connect to database if not already connected"""
        if self.db_conn is None:
            self.db_conn = psycopg2.connect(
                host=DB_HOST,
                port=DB_PORT,
                database=DB_NAME,
                user=DB_USER,
                password=DB_PASSWORD
            )
            self._owns_connection = True

        self.health_calc = HealthCalculator(self.db_conn)
        self.tracker = EventTracker(self.db_conn)
        self.usage_tracker = UsageTracker(self.db_conn)

    def close(self):
        """Close database connection if we own it"""
        if self._owns_connection and self.db_conn:
            self.db_conn.close()
            self.db_conn = None

    def get_period_stats(self, days: int = 7) -> DigestStats:
        """Get statistics for the digest period"""
        self.connect()
        cursor = self.db_conn.cursor()

        period_end = datetime.now()
        period_start = period_end - timedelta(days=days)

        # Reflections applied
        cursor.execute("""
            SELECT COUNT(*) FROM skill_reflections
            WHERE created_at >= %s
            AND (reviewed_by IS NULL OR reviewed_by != 'auto-skipped')
        """, (period_start,))
        reflections_applied = cursor.fetchone()[0]

        # Skills updated
        cursor.execute("""
            SELECT COUNT(DISTINCT skill_name) FROM skill_reflections
            WHERE created_at >= %s
            AND (reviewed_by IS NULL OR reviewed_by != 'auto-skipped')
        """, (period_start,))
        skills_updated = cursor.fetchone()[0]

        # Feedback given
        cursor.execute("""
            SELECT COUNT(*) FROM skill_reflections
            WHERE feedback_at >= %s
        """, (period_start,))
        feedback_given = cursor.fetchone()[0]

        # Skills used
        cursor.execute("""
            SELECT COUNT(*) FROM skill_usage
            WHERE created_at >= %s
        """, (period_start,))
        skills_used = cursor.fetchone()[0]

        # Health changes (from evolution_events)
        # Note: These events are only created when health crosses thresholds
        health_improved = 0
        health_declined = 0
        try:
            cursor.execute("""
                SELECT
                    COUNT(*) FILTER (WHERE event_type = 'health_alert'
                        AND (event_data->>'trigger')::text LIKE '%%improved%%') as improved,
                    COUNT(*) FILTER (WHERE event_type = 'health_alert'
                        AND (event_data->>'trigger')::text LIKE '%%declined%%') as declined
                FROM evolution_events
                WHERE created_at >= %s
            """, (period_start,))
            row = cursor.fetchone()
            if row:
                health_improved = row[0] or 0
                health_declined = row[1] or 0
        except Exception:
            pass  # Table might not exist or be empty

        # Attention needed
        attention_skills = self.health_calc.get_attention_needed()
        attention_needed = len(attention_skills)

        return DigestStats(
            period_start=period_start,
            period_end=period_end,
            reflections_applied=reflections_applied,
            skills_updated=skills_updated,
            feedback_given=feedback_given,
            skills_used=skills_used,
            health_improved=health_improved,
            health_declined=health_declined,
            attention_needed=attention_needed
        )

    def generate_weekly_digest(self, days: int = 7) -> str:
        """Generate weekly digest content"""
        self.connect()
        stats = self.get_period_stats(days)

        # Get top events
        events = self.tracker.get_events(days=days, limit=20)

        # Get health summary
        all_health = self.health_calc.get_all_health(order_by='health_score DESC')
        attention_skills = self.health_calc.get_attention_needed()

        # Get most used skills
        usage_counts = self.usage_tracker.get_most_used_skills(days, 5)

        # Build digest
        digest = f"""# 📊 Weekly Evolution Digest
_{stats.period_start.strftime('%Y-%m-%d')} to {stats.period_end.strftime('%Y-%m-%d')}_

## 📈 Summary

| Metric | This Week |
|--------|-----------|
| Reflections Applied | {stats.reflections_applied} |
| Skills Updated | {stats.skills_updated} |
| Feedback Given | {stats.feedback_given} |
| Skill Usages | {stats.skills_used} |
| Skills Needing Attention | {stats.attention_needed} |

"""

        # Activity section
        if events:
            digest += "## 🔄 Recent Activity\n\n"
            for event in events[:10]:
                date = event.created_at.strftime('%m-%d')
                digest += f"- `{date}` {event.event_emoji} **{event.skill_name}**: {event.description[:50]}\n"
            digest += "\n"

        # Usage section
        if usage_counts:
            digest += "## 🔥 Most Used Skills\n\n"
            for skill, count in usage_counts:
                digest += f"- **{skill}**: {count} session(s)\n"
            digest += "\n"

        # Attention section
        if attention_skills:
            digest += "## ⚠️ Needs Attention\n\n"
            for skill in attention_skills[:5]:
                digest += f"- **{skill.skill_name}** (Score: {skill.health_score:.0f}): {skill.attention_reason}\n"
            digest += "\n"

        # Health leaderboard
        if all_health:
            digest += "## 💚 Healthiest Skills\n\n"
            for skill in all_health[:5]:
                digest += f"- **{skill.skill_name}**: {skill.health_score:.0f}/100 {skill.health_emoji}\n"
            digest += "\n"

        # Recommendations
        digest += """## 🎯 Recommendations

"""
        if stats.attention_needed > 0:
            digest += f"1. Review {stats.attention_needed} skill(s) needing attention\n"

        unrated = self._get_unrated_count()
        if unrated > 0:
            digest += f"2. Rate {unrated} unrated learning(s) with `/evolution-feedback`\n"

        if stats.skills_used == 0:
            digest += "3. Track skill usage by using skills in your conversations\n"
        else:
            digest += "3. Keep using skills - usage data improves health scores\n"

        digest += f"""
---
_Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}_
_View full report: `/evolution-report`_
_Give feedback: `/evolution-feedback`_
"""

        return digest

    def _get_unrated_count(self) -> int:
        """Get count of unrated learnings"""
        cursor = self.db_conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) FROM skill_reflections
            WHERE user_feedback IS NULL
            AND (reviewed_by IS NULL OR reviewed_by != 'auto-skipped')
        """)
        return cursor.fetchone()[0]

    def generate_attention_alert(self) -> Optional[str]:
        """
        Generate attention alert if there are skills needing review.
        Returns None if no attention needed.
        """
        self.connect()
        attention_skills = self.health_calc.get_attention_needed()

        if not attention_skills:
            return None

        # Check for critical issues
        critical = [s for s in attention_skills if s.health_score < 40]
        warnings = [s for s in attention_skills if 40 <= s.health_score < 60]

        alert = "# ⚠️ Skill Attention Alert\n\n"

        if critical:
            alert += "## 🔴 Critical (Score < 40)\n\n"
            for skill in critical:
                alert += f"- **{skill.skill_name}** ({skill.health_score:.0f}): {skill.attention_reason}\n"
            alert += "\n"

        if warnings:
            alert += "## 🟠 Warning (Score 40-60)\n\n"
            for skill in warnings:
                alert += f"- **{skill.skill_name}** ({skill.health_score:.0f}): {skill.attention_reason}\n"
            alert += "\n"

        alert += f"""---
_Run `/evolution-feedback` to review and rate learnings_
_Run `/evolution-report --attention` to see details_
"""

        return alert

    def save_digest(self, days: int = 7) -> Path:
        """Generate and save weekly digest to file"""
        digest = self.generate_weekly_digest(days)
        self.DIGEST_FILE.write_text(digest)
        return self.DIGEST_FILE

    def save_attention_alert(self) -> Optional[Path]:
        """Generate and save attention alert if needed"""
        alert = self.generate_attention_alert()
        if alert:
            self.ATTENTION_FILE.write_text(alert)
            return self.ATTENTION_FILE
        elif self.ATTENTION_FILE.exists():
            self.ATTENTION_FILE.unlink()
        return None

    def should_send_digest(self, last_sent: Optional[datetime] = None,
                           interval_days: int = 7) -> bool:
        """Check if enough time has passed to send a new digest"""
        if last_sent is None:
            return True
        return datetime.now() - last_sent >= timedelta(days=interval_days)


def generate_and_save_digest(days: int = 7) -> Dict:
    """
    Convenience function for automation.
    Generates digest and attention alert, saves to files.

    Returns:
        Dict with paths to generated files
    """
    generator = DigestGenerator()
    try:
        digest_path = generator.save_digest(days)
        attention_path = generator.save_attention_alert()

        return {
            'digest_path': str(digest_path),
            'attention_path': str(attention_path) if attention_path else None,
            'generated_at': datetime.now().isoformat()
        }
    finally:
        generator.close()


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Evolution Digest Generator')
    parser.add_argument('--days', type=int, default=7, help='Days to include in digest')
    parser.add_argument('--save', action='store_true', help='Save digest to file')
    parser.add_argument('--attention-only', action='store_true', help='Only generate attention alert')

    args = parser.parse_args()

    generator = DigestGenerator()
    try:
        if args.attention_only:
            alert = generator.generate_attention_alert()
            if alert:
                print(alert)
            else:
                print("No skills need attention! 🎉")
        elif args.save:
            result = generate_and_save_digest(args.days)
            print(f"Digest saved to: {result['digest_path']}")
            if result['attention_path']:
                print(f"Attention alert saved to: {result['attention_path']}")
        else:
            print(generator.generate_weekly_digest(args.days))
    finally:
        generator.close()
