"""
Feedback Collector

Interactive collection of user feedback on learnings.
Supports rating learnings and reverting bad ones.
"""

import psycopg2
from typing import Optional, Dict, List
from dataclasses import dataclass
from datetime import datetime

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD

from .health import HealthCalculator
from .tracker import EventTracker


@dataclass
class UnratedLearning:
    """A learning awaiting feedback"""
    id: str
    skill_name: str
    signal_text: str
    what_changed: str
    confidence: str
    source_session: str
    created_at: datetime

    @property
    def confidence_emoji(self) -> str:
        """Get confidence level emoji"""
        emojis = {'high': '🔒', 'medium': '🔓', 'low': '❓'}
        return emojis.get(self.confidence, '❓')


class FeedbackCollector:
    """Collects and records user feedback on learnings"""

    FEEDBACK_OPTIONS = {
        '1': ('helpful', '👍 Helpful', 'It improved my workflow'),
        '2': ('not_helpful', '👎 Not helpful', "It didn't make a difference"),
        '3': ('reverted', '⏪ Revert', 'It actually made things worse'),
        '4': ('skip', '⏭️ Skip', "I haven't used this skill since"),
        '5': ('note', '📝 Note', 'Add a note without rating'),
    }

    def __init__(self, db_conn=None):
        self.db_conn = db_conn
        self._owns_connection = False
        self.health_calc = None
        self.tracker = None

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

    def close(self):
        """Close database connection if we own it"""
        if self._owns_connection and self.db_conn:
            self.db_conn.close()
            self.db_conn = None

    def get_unrated_learnings(self, limit: int = 10) -> List[UnratedLearning]:
        """Get learnings that haven't been rated yet"""
        self.connect()
        cursor = self.db_conn.cursor()

        cursor.execute("""
            SELECT id, skill_name, signal_text, what_changed, confidence, source_session,
                   COALESCE(created_at, applied_at) as created_at
            FROM skill_reflections
            WHERE user_feedback IS NULL
            AND (reviewed_by IS NULL OR reviewed_by NOT IN ('auto-skipped'))
            AND skill_name != 'NEW_SKILL'
            ORDER BY COALESCE(created_at, applied_at) DESC
            LIMIT %s
        """, (limit,))

        learnings = []
        for row in cursor.fetchall():
            learnings.append(UnratedLearning(
                id=str(row[0]),
                skill_name=row[1],
                signal_text=row[2],
                what_changed=row[3],
                confidence=row[4],
                source_session=row[5],
                created_at=row[6]
            ))

        return learnings

    def get_unrated_count(self) -> int:
        """Get count of unrated learnings"""
        self.connect()
        cursor = self.db_conn.cursor()

        cursor.execute("""
            SELECT COUNT(*)
            FROM skill_reflections
            WHERE user_feedback IS NULL
            AND (reviewed_by IS NULL OR reviewed_by NOT IN ('auto-skipped'))
            AND skill_name != 'NEW_SKILL'
        """)

        return cursor.fetchone()[0]

    def record_feedback(self,
                        reflection_id: str,
                        feedback: str,
                        notes: Optional[str] = None) -> Dict:
        """
        Record feedback for a learning.

        Args:
            reflection_id: ID of the reflection
            feedback: One of 'helpful', 'not_helpful', 'reverted'
            notes: Optional feedback notes

        Returns:
            Dict with result info including health score change
        """
        if feedback not in ('helpful', 'not_helpful', 'reverted'):
            raise ValueError(f"Invalid feedback: {feedback}")

        self.connect()
        cursor = self.db_conn.cursor()

        # Get current skill info
        cursor.execute("""
            SELECT sr.skill_name, sh.health_score
            FROM skill_reflections sr
            LEFT JOIN skill_health sh ON sr.skill_name = sh.skill_name
            WHERE sr.id = %s
        """, (reflection_id,))
        row = cursor.fetchone()
        if not row:
            return {'error': f'Reflection not found: {reflection_id}'}

        skill_name = row[0]
        old_health = row[1] or 50.0

        # Record feedback
        cursor.execute("""
            UPDATE skill_reflections
            SET user_feedback = %s,
                feedback_at = NOW(),
                feedback_notes = %s
            WHERE id = %s
        """, (feedback, notes, reflection_id))

        # Recalculate health
        cursor.execute("SELECT recalculate_skill_health(%s)", (skill_name,))
        new_health = cursor.fetchone()[0] or 50.0

        # Record evolution event
        event_type = f'feedback_{feedback}' if feedback != 'reverted' else 'learning_reverted'
        self.tracker.record_event(
            skill_name=skill_name,
            event_type=event_type,
            event_data={
                'reflection_id': reflection_id,
                'notes': notes,
                'previous_health': old_health,
                'new_health': new_health
            }
        )

        self.db_conn.commit()

        return {
            'skill_name': skill_name,
            'feedback': feedback,
            'old_health': old_health,
            'new_health': new_health,
            'health_change': new_health - old_health
        }

    def revert_learning(self,
                        reflection_id: str,
                        reason: Optional[str] = None) -> Dict:
        """
        Revert a learning (marks as reverted and optionally git reverts).

        Note: Git revert functionality requires the git_manager module.
        This method handles the database side.

        Args:
            reflection_id: ID of the reflection to revert
            reason: Optional reason for reverting

        Returns:
            Dict with result info
        """
        self.connect()
        cursor = self.db_conn.cursor()

        # Get reflection info
        cursor.execute("""
            SELECT skill_name, git_commit, what_changed
            FROM skill_reflections
            WHERE id = %s
        """, (reflection_id,))
        row = cursor.fetchone()
        if not row:
            return {'error': f'Reflection not found: {reflection_id}'}

        skill_name, git_commit, what_changed = row

        # Mark as reverted
        cursor.execute("""
            UPDATE skill_reflections
            SET user_feedback = 'reverted',
                feedback_at = NOW(),
                feedback_notes = %s,
                reverted_at = NOW()
            WHERE id = %s
        """, (reason, reflection_id))

        # Recalculate health
        cursor.execute("SELECT recalculate_skill_health(%s)", (skill_name,))
        new_health = cursor.fetchone()[0] or 50.0

        # Record evolution event
        self.tracker.record_event(
            skill_name=skill_name,
            event_type='learning_reverted',
            event_data={
                'reflection_id': reflection_id,
                'reason': reason,
                'what_changed': what_changed,
                'original_commit': git_commit
            }
        )

        self.db_conn.commit()

        return {
            'skill_name': skill_name,
            'reverted': True,
            'git_commit': git_commit,
            'new_health': new_health,
            'message': f"Learning reverted for {skill_name}"
        }

    def display_learning(self, learning: UnratedLearning) -> str:
        """Format a learning for display"""
        date_str = learning.created_at.strftime('%Y-%m-%d') if learning.created_at else 'Unknown'

        lines = [
            "─" * 60,
            f"Learning: {learning.skill_name} ({date_str})",
            "─" * 60,
            f"Signal: \"{learning.signal_text}\"",
            f"Change: {learning.what_changed}",
            f"Confidence: {learning.confidence_emoji} {learning.confidence.upper()}",
            f"Source: {learning.source_session}",
            "",
            "Has this learning been helpful?",
            ""
        ]

        for key, (_, label, desc) in self.FEEDBACK_OPTIONS.items():
            lines.append(f"  [{key}] {label:<16} - {desc}")

        return '\n'.join(lines)

    def run_interactive(self, limit: int = 10) -> Dict:
        """
        Run interactive feedback session.

        Returns:
            Dict with summary of feedback collected
        """
        self.connect()

        learnings = self.get_unrated_learnings(limit)

        if not learnings:
            return {
                'message': "No unrated learnings found. All caught up! 🎉",
                'rated': 0
            }

        print("🗳️  Learning Feedback")
        print("═" * 64)
        print(f"Rate recent skill updates to improve future reflections.")
        print(f"{len(learnings)} unrated learning(s) found.")
        print()

        stats = {'helpful': 0, 'not_helpful': 0, 'reverted': 0, 'skipped': 0, 'notes': 0}

        for i, learning in enumerate(learnings, 1):
            print(f"\n{self.display_learning(learning)}")
            print(f"\n[Learning {i}/{len(learnings)}]")

            choice = input("\nYour choice: ").strip()

            if choice not in self.FEEDBACK_OPTIONS:
                print("Invalid choice, skipping...")
                stats['skipped'] += 1
                continue

            feedback_key, label, _ = self.FEEDBACK_OPTIONS[choice]

            if feedback_key == 'skip':
                print("⏭️ Skipped")
                stats['skipped'] += 1
                continue

            if feedback_key == 'note':
                note = input("Note: ").strip()
                if note:
                    # Just add note without changing feedback status
                    cursor = self.db_conn.cursor()
                    cursor.execute("""
                        UPDATE skill_reflections
                        SET feedback_notes = COALESCE(feedback_notes || ' | ', '') || %s
                        WHERE id = %s
                    """, (note, learning.id))
                    self.db_conn.commit()
                    print("📝 Note added")
                    stats['notes'] += 1
                continue

            # Get optional note
            note = input("Optional note (press Enter to skip): ").strip() or None

            # Record feedback
            if feedback_key == 'reverted':
                result = self.revert_learning(learning.id, note)
            else:
                result = self.record_feedback(learning.id, feedback_key, note)

            if 'error' in result:
                print(f"❌ Error: {result['error']}")
            else:
                health_change = result.get('health_change', 0)
                change_str = f"+{health_change:.0f}" if health_change >= 0 else f"{health_change:.0f}"
                print(f"\n✅ Feedback recorded: {feedback_key}")
                print(f"   Health score: {result.get('old_health', 50):.0f} → {result.get('new_health', 50):.0f} ({change_str})")
                stats[feedback_key] += 1

        # Summary
        print("\n" + "═" * 64)
        print("📊 FEEDBACK SUMMARY")
        print("─" * 60)
        total_rated = stats['helpful'] + stats['not_helpful'] + stats['reverted']
        print(f"Rated: {total_rated} learning(s)")
        print(f"  • Helpful:     {stats['helpful']}")
        print(f"  • Not helpful: {stats['not_helpful']}")
        print(f"  • Reverted:    {stats['reverted']}")
        print(f"  • Skipped:     {stats['skipped']}")
        if stats['notes']:
            print(f"  • Notes added: {stats['notes']}")
        print("\nThank you for your feedback!")

        return {
            'rated': total_rated,
            'stats': stats
        }


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Feedback Collector')
    parser.add_argument('--count', action='store_true', help='Just show unrated count')
    parser.add_argument('--limit', type=int, default=10, help='Max learnings to rate')

    args = parser.parse_args()

    collector = FeedbackCollector()
    try:
        if args.count:
            count = collector.get_unrated_count()
            print(f"Unrated learnings: {count}")
        else:
            collector.run_interactive(limit=args.limit)
    finally:
        collector.close()
