"""
Skill Usage Tracker

Tracks when skills are used/referenced in conversations.
Feeds into health score calculations via usage metrics.
"""

import psycopg2
import re
from typing import Optional, List, Dict, Set
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD

from .tracker import EventTracker


@dataclass
class SkillUsage:
    """Record of skill usage in a session"""
    id: str
    skill_name: str
    session_id: str
    usage_context: Optional[str]
    created_at: datetime


class UsageTracker:
    """Tracks and queries skill usage"""

    def __init__(self, db_conn=None):
        self.db_conn = db_conn
        self._owns_connection = False
        self.event_tracker = None
        self._known_skills: Set[str] = set()

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

        self.event_tracker = EventTracker(self.db_conn)

    def close(self):
        """Close database connection if we own it"""
        if self._owns_connection and self.db_conn:
            self.db_conn.close()
            self.db_conn = None

    def get_known_skills(self) -> Set[str]:
        """Get list of known skill names from filesystem"""
        if self._known_skills:
            return self._known_skills

        skills_dir = Path.home() / '.claude' / 'skills'
        if skills_dir.exists():
            for skill_file in skills_dir.glob('*.md'):
                # Extract skill name from filename
                self._known_skills.add(skill_file.stem)

        return self._known_skills

    def detect_skill_usage(self, text: str) -> List[str]:
        """
        Detect skill invocations in text.

        Looks for patterns like:
        - /skill-name (direct invocation)
        - [skill-name] (referenced in discussion)
        - skill_name skill (mentioned by name)

        Returns list of detected skill names.
        """
        detected = set()
        known_skills = self.get_known_skills()

        # Pattern 1: Direct slash commands /skill-name
        slash_pattern = r'/([a-z][a-z0-9-]*)'
        for match in re.finditer(slash_pattern, text.lower()):
            skill = match.group(1)
            if skill in known_skills:
                detected.add(skill)

        # Pattern 2: Skill name in brackets [skill-name]
        bracket_pattern = r'\[([a-z][a-z0-9-]*)\]'
        for match in re.finditer(bracket_pattern, text.lower()):
            skill = match.group(1)
            if skill in known_skills:
                detected.add(skill)

        # Pattern 3: Direct mentions of known skills
        for skill in known_skills:
            # Match skill name as whole word (with word boundaries)
            if re.search(rf'\b{re.escape(skill)}\b', text.lower()):
                detected.add(skill)

        return list(detected)

    def record_usage(self,
                     skill_name: str,
                     session_id: str,
                     usage_context: Optional[str] = None,
                     record_event: bool = True) -> Optional[str]:
        """
        Record a skill usage.

        Args:
            skill_name: Name of the skill
            session_id: Session ID where skill was used
            usage_context: Brief description of how it was used
            record_event: Whether to also record an evolution event

        Returns:
            Usage ID if recorded, None if duplicate
        """
        self.connect()
        cursor = self.db_conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO skill_usage (skill_name, session_id, usage_context)
                VALUES (%s, %s, %s)
                ON CONFLICT (skill_name, session_id) DO NOTHING
                RETURNING id
            """, (skill_name, session_id, usage_context))

            result = cursor.fetchone()
            self.db_conn.commit()

            if result:
                usage_id = str(result[0])

                # Record evolution event
                if record_event:
                    self.event_tracker.record_event(
                        skill_name=skill_name,
                        event_type='skill_used',
                        event_data={
                            'session_id': session_id,
                            'usage_context': usage_context,
                            'invocation_type': 'direct' if usage_context and '/' in usage_context else 'referenced'
                        },
                        session_id=session_id
                    )

                return usage_id

            return None  # Duplicate - already recorded for this session

        except Exception as e:
            self.db_conn.rollback()
            raise e

    def record_session_usage(self,
                             session_id: str,
                             transcript: str,
                             record_events: bool = True) -> List[str]:
        """
        Analyze a session transcript and record all skill usage.

        Args:
            session_id: Session identifier
            transcript: Full session transcript text
            record_events: Whether to record evolution events

        Returns:
            List of skills that were used
        """
        skills_used = self.detect_skill_usage(transcript)

        for skill in skills_used:
            # Try to extract context around the skill mention
            context = self._extract_context(transcript, skill)
            self.record_usage(skill, session_id, context, record_events)

        return skills_used

    def _extract_context(self, text: str, skill_name: str, context_chars: int = 100) -> str:
        """Extract context around a skill mention"""
        # Find the skill mention
        match = re.search(rf'(.{{0,{context_chars}}}\b{re.escape(skill_name)}\b.{{0,{context_chars}}})',
                          text, re.IGNORECASE)
        if match:
            context = match.group(1).strip()
            # Clean up and truncate
            context = re.sub(r'\s+', ' ', context)[:200]
            return context
        return f"Used {skill_name}"

    def get_usage(self,
                  skill_name: Optional[str] = None,
                  days: int = 30,
                  limit: int = 100) -> List[SkillUsage]:
        """
        Get skill usage records.

        Args:
            skill_name: Filter by skill name
            days: Look back N days
            limit: Maximum records to return

        Returns:
            List of usage records
        """
        self.connect()
        cursor = self.db_conn.cursor()

        query = """
            SELECT id, skill_name, session_id, usage_context, created_at
            FROM skill_usage
            WHERE created_at > NOW() - INTERVAL '%s days'
        """
        params = [days]

        if skill_name:
            query += " AND skill_name = %s"
            params.append(skill_name)

        query += " ORDER BY created_at DESC LIMIT %s"
        params.append(limit)

        cursor.execute(query, params)

        usages = []
        for row in cursor.fetchall():
            usages.append(SkillUsage(
                id=str(row[0]),
                skill_name=row[1],
                session_id=row[2],
                usage_context=row[3],
                created_at=row[4]
            ))

        return usages

    def get_usage_counts(self, days: int = 30) -> Dict[str, int]:
        """Get usage counts by skill for the last N days"""
        self.connect()
        cursor = self.db_conn.cursor()

        cursor.execute("""
            SELECT skill_name, COUNT(*) as usage_count
            FROM skill_usage
            WHERE created_at > NOW() - INTERVAL '%s days'
            GROUP BY skill_name
            ORDER BY usage_count DESC
        """, (days,))

        return {row[0]: row[1] for row in cursor.fetchall()}

    def get_skill_usage_count(self, skill_name: str, days: int = 30) -> int:
        """Get usage count for a specific skill"""
        self.connect()
        cursor = self.db_conn.cursor()

        cursor.execute("""
            SELECT COUNT(*) FROM skill_usage
            WHERE skill_name = %s
            AND created_at > NOW() - INTERVAL '%s days'
        """, (skill_name, days))

        return cursor.fetchone()[0]

    def get_most_used_skills(self, days: int = 30, limit: int = 10) -> List[tuple]:
        """Get most used skills in the last N days"""
        self.connect()
        cursor = self.db_conn.cursor()

        cursor.execute("""
            SELECT skill_name, COUNT(*) as usage_count
            FROM skill_usage
            WHERE created_at > NOW() - INTERVAL '%s days'
            GROUP BY skill_name
            ORDER BY usage_count DESC
            LIMIT %s
        """, (days, limit))

        return [(row[0], row[1]) for row in cursor.fetchall()]

    def get_unused_skills(self, days: int = 30) -> List[str]:
        """Get skills that haven't been used in the last N days"""
        known_skills = self.get_known_skills()
        used_skills = set(self.get_usage_counts(days).keys())
        return list(known_skills - used_skills)


def track_session_usage(session_id: str, transcript: str) -> List[str]:
    """
    Convenience function to track usage for a session.

    Args:
        session_id: Session identifier
        transcript: Full session transcript

    Returns:
        List of skills that were detected and recorded
    """
    tracker = UsageTracker()
    try:
        return tracker.record_session_usage(session_id, transcript)
    finally:
        tracker.close()


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Skill Usage Tracker')
    parser.add_argument('--days', type=int, default=30, help='Days to look back')
    parser.add_argument('--skill', help='Filter by skill name')
    parser.add_argument('--top', type=int, default=10, help='Show top N skills')
    parser.add_argument('--unused', action='store_true', help='Show unused skills')
    parser.add_argument('--test', help='Test skill detection on text')

    args = parser.parse_args()

    tracker = UsageTracker()
    try:
        if args.test:
            print(f"Detected skills: {tracker.detect_skill_usage(args.test)}")
        elif args.unused:
            print("=== Unused Skills (Last {} Days) ===".format(args.days))
            for skill in tracker.get_unused_skills(args.days):
                print(f"  • {skill}")
        else:
            print(f"=== Most Used Skills (Last {args.days} Days) ===")
            for skill, count in tracker.get_most_used_skills(args.days, args.top):
                print(f"  {skill}: {count} sessions")
    finally:
        tracker.close()
