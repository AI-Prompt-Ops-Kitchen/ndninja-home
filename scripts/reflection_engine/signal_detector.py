"""
Signal Detector - Finds correction signals in conversation summaries
"""

import re
from typing import List, Dict, Optional
from dataclasses import dataclass
from config import CORRECTION_PATTERNS, PATTERN_MIN_OCCURRENCES


@dataclass
class Signal:
    """Represents a detected correction signal"""
    signal_type: str  # 'correction', 'pattern', 'preference'
    signal_text: str  # Exact user quote
    confidence: str  # 'high', 'medium', 'low'
    context: str  # Surrounding conversation context
    source_session: str
    occurrence_count: int = 1


class SignalDetector:
    """Detects correction signals in conversation summaries"""

    def __init__(self):
        self.patterns = [re.compile(p, re.IGNORECASE) for p in CORRECTION_PATTERNS]

    def detect_signals(self, conversation_summaries: List[Dict]) -> List[Signal]:
        """
        Analyzes conversation summaries for correction signals.

        Args:
            conversation_summaries: List of conversation summary dicts

        Returns:
            List of Signal objects with detected corrections
        """
        signals = []

        for summary in conversation_summaries:
            # Extract signals from summary text
            signals.extend(self._detect_from_summary(summary))

            # Detect patterns from repeated topics
            signals.extend(self._detect_from_topics(summary))

            # Detect from key decisions (often indicate corrections)
            signals.extend(self._detect_from_decisions(summary))

        # Merge duplicate signals and update occurrence counts
        signals = self._merge_duplicate_signals(signals)

        return signals

    def _detect_from_summary(self, summary: Dict) -> List[Signal]:
        """Detect explicit corrections in summary text"""
        signals = []
        summary_text = summary.get('summary', '')
        session_id = summary.get('session_id', 'unknown')

        # Check for correction keywords
        correction_keywords = [
            'corrected', 'fixed', 'actually', 'instead',
            'should use', 'changed to', 'updated to'
        ]

        for keyword in correction_keywords:
            if keyword.lower() in summary_text.lower():
                # Extract context around the keyword
                context = self._extract_context(summary_text, keyword)

                signals.append(Signal(
                    signal_type='correction',
                    signal_text=context,
                    confidence='medium',  # Will be upgraded by analyzer
                    context=summary_text,
                    source_session=session_id
                ))

        # Apply regex patterns
        for pattern in self.patterns:
            matches = pattern.finditer(summary_text)
            for match in matches:
                signals.append(Signal(
                    signal_type='correction',
                    signal_text=match.group(0),
                    confidence='high',  # Explicit pattern match
                    context=summary_text,
                    source_session=session_id
                ))

        return signals

    def _detect_from_topics(self, summary: Dict) -> List[Signal]:
        """Detect patterns from repeated topics across sessions"""
        # This will be enhanced to check multiple sessions
        # For now, just flag repeated topics in current session
        signals = []
        topics = summary.get('topics_discussed', [])
        session_id = summary.get('session_id', 'unknown')

        # Check for repeated topics (indicates unlearned pattern)
        topic_counts = {}
        for topic in topics:
            if isinstance(topic, str):
                topic_counts[topic] = topic_counts.get(topic, 0) + 1

        for topic, count in topic_counts.items():
            if count >= PATTERN_MIN_OCCURRENCES:
                signals.append(Signal(
                    signal_type='pattern',
                    signal_text=f"Repeated topic: {topic}",
                    confidence='medium',
                    context=f"Topic '{topic}' appeared {count} times",
                    source_session=session_id,
                    occurrence_count=count
                ))

        return signals

    def _detect_from_decisions(self, summary: Dict) -> List[Signal]:
        """Detect preferences from key decisions"""
        signals = []
        decisions = summary.get('key_decisions', [])
        session_id = summary.get('session_id', 'unknown')

        for decision in decisions:
            if isinstance(decision, str):
                # Decisions often encode preferences
                if any(keyword in decision.lower() for keyword in ['prefer', 'use', 'choose', 'default']):
                    signals.append(Signal(
                        signal_type='preference',
                        signal_text=decision,
                        confidence='medium',
                        context=decision,
                        source_session=session_id
                    ))

        return signals

    def _extract_context(self, text: str, keyword: str, window: int = 100) -> str:
        """Extract context around a keyword"""
        keyword_lower = keyword.lower()
        text_lower = text.lower()

        idx = text_lower.find(keyword_lower)
        if idx == -1:
            return text[:200]  # Fallback to beginning

        start = max(0, idx - window)
        end = min(len(text), idx + len(keyword) + window)

        return text[start:end].strip()

    def _merge_duplicate_signals(self, signals: List[Signal]) -> List[Signal]:
        """Merge duplicate signals and count occurrences"""
        # Group by signal_text (normalized)
        signal_groups = {}

        for signal in signals:
            normalized_text = signal.signal_text.strip().lower()

            if normalized_text in signal_groups:
                # Increment occurrence count
                signal_groups[normalized_text].occurrence_count += 1

                # Upgrade confidence if multiple occurrences
                if signal_groups[normalized_text].occurrence_count >= 3:
                    signal_groups[normalized_text].confidence = 'high'
                elif signal_groups[normalized_text].occurrence_count >= 2:
                    signal_groups[normalized_text].confidence = 'medium'
            else:
                signal_groups[normalized_text] = signal

        return list(signal_groups.values())

    def detect_from_single_session(self, session_id: str, db_conn) -> List[Signal]:
        """
        Detect signals from a single session by querying the database.

        Args:
            session_id: The session ID to analyze
            db_conn: Database connection object

        Returns:
            List of detected signals
        """
        cursor = db_conn.cursor()

        # Query conversation summary
        cursor.execute("""
            SELECT session_id, summary, action_items, key_decisions,
                   topics_discussed, problems_solved
            FROM conversation_summaries
            WHERE session_id = %s
        """, (session_id,))

        row = cursor.fetchone()
        if not row:
            return []

        summary = {
            'session_id': row[0],
            'summary': row[1],
            'action_items': row[2] or [],
            'key_decisions': row[3] or [],
            'topics_discussed': row[4] or [],
            'problems_solved': row[5] or []
        }

        return self.detect_signals([summary])

    def detect_from_recent_sessions(self, days: int, db_conn) -> List[Signal]:
        """
        Detect signals from recent sessions.

        Args:
            days: Number of days to look back
            db_conn: Database connection object

        Returns:
            List of detected signals (deduplicated against already processed signals)
        """
        cursor = db_conn.cursor()

        # Query recent conversation summaries
        cursor.execute("""
            SELECT session_id, summary, action_items, key_decisions,
                   topics_discussed, problems_solved
            FROM conversation_summaries
            WHERE created_at >= NOW() - INTERVAL '%s days'
              AND app_source = 'code'
            ORDER BY created_at DESC
        """, (days,))

        rows = cursor.fetchall()
        summaries = []

        for row in rows:
            summaries.append({
                'session_id': row[0],
                'summary': row[1],
                'action_items': row[2] or [],
                'key_decisions': row[3] or [],
                'topics_discussed': row[4] or [],
                'problems_solved': row[5] or []
            })

        signals = self.detect_signals(summaries)

        # Filter out already processed signals
        signals = self._filter_processed_signals(signals, db_conn)

        return signals

    def _filter_processed_signals(self, signals: List[Signal], db_conn) -> List[Signal]:
        """
        Filter out signals that have already been processed.

        Uses SESSION-BASED deduplication: if ANY signal from a session has been
        processed, skip ALL signals from that session. This prevents the infinite
        loop bug where different text extracts from the same session would bypass
        text-based deduplication.

        Args:
            signals: List of detected signals
            db_conn: Database connection object

        Returns:
            Filtered list of signals (only from unprocessed sessions)
        """
        if not signals:
            return []

        cursor = db_conn.cursor()

        # Get all sessions that have been processed in the last 30 days
        # Session-based deduplication prevents infinite loops from variable text extracts
        cursor.execute("""
            SELECT DISTINCT source_session
            FROM skill_reflections
            WHERE applied_at >= NOW() - INTERVAL '30 days'
              AND source_session IS NOT NULL
        """)

        processed_sessions = set()
        for row in cursor.fetchall():
            if row[0]:
                processed_sessions.add(row[0])

        # Filter out signals from already processed sessions
        filtered_signals = []
        for signal in signals:
            if signal.source_session not in processed_sessions:
                filtered_signals.append(signal)

        return filtered_signals
