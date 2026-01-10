#!/usr/bin/env python3
"""
Reflection Engine - Main Entry Point

Analyzes conversation corrections and updates skill files with learnings.
"""

import sys
import argparse
import psycopg2
from pathlib import Path
from typing import Optional

# Add script directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from signal_detector import SignalDetector, Signal
from analyzer import Analyzer, Reflection
from skill_updater import SkillUpdater
from git_manager import GitManager
from notifications import NotificationManager
from config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD, HOME_DIR


class ReflectionEngine:
    """Main reflection engine coordinator"""

    def __init__(self):
        self.detector = SignalDetector()
        self.analyzer = Analyzer()
        self.updater = SkillUpdater()
        self.git = GitManager()
        self.notifications = NotificationManager(
            summary_file=HOME_DIR / '.claude' / 'reflection-summary.md'
        )
        self.db_conn = None

    def connect_db(self):
        """Connect to Claude Memory database"""
        try:
            self.db_conn = psycopg2.connect(
                host=DB_HOST,
                port=DB_PORT,
                database=DB_NAME,
                user=DB_USER,
                password=DB_PASSWORD
            )
            return True
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            return False

    def close_db(self):
        """Close database connection"""
        if self.db_conn:
            self.db_conn.close()

    def reflect(self,
                session_id: Optional[str] = None,
                days: int = 1,
                skill_filter: Optional[str] = None,
                dry_run: bool = False,
                auto_approve: bool = False) -> dict:
        """
        Run reflection process.

        Args:
            session_id: Specific session to analyze (or None for recent sessions)
            days: Number of days to look back (if no session_id)
            skill_filter: Only update this skill
            dry_run: Preview without applying
            auto_approve: Auto-approve high confidence updates

        Returns:
            Dict with results summary
        """
        print("🧠 Reflection Engine v1.0.0")
        print("=" * 60)

        # Connect to database
        if not self.connect_db():
            return {'error': 'Database connection failed'}

        try:
            # Step 1: Detect signals
            print("\n📡 Detecting signals...")
            if session_id:
                signals = self.detector.detect_from_single_session(session_id, self.db_conn)
                print(f"   Analyzing session: {session_id}")
            else:
                signals = self.detector.detect_from_recent_sessions(days, self.db_conn)
                print(f"   Analyzing last {days} day(s)")

            if not signals:
                print("   ✓ No correction signals detected")
                return {'signals': 0, 'reflections': 0, 'applied': 0}

            print(f"   ✓ Detected {len(signals)} signal(s)")

            # Step 2: Analyze with LLM Council
            print("\n🔍 Analyzing with LLM Council...")
            reflections = self.analyzer.analyze_with_council(signals)

            if not reflections:
                print("   ✓ No actionable reflections identified")
                return {'signals': len(signals), 'reflections': 0, 'applied': 0}

            print(f"   ✓ Generated {len(reflections)} reflection(s)")

            # Filter out NEW_SKILL placeholders (no actual skill to update)
            new_skill_reflections = [r for r in reflections if r.skill_name == 'NEW_SKILL']
            reflections = [r for r in reflections if r.skill_name != 'NEW_SKILL']

            if new_skill_reflections:
                print(f"   ℹ Skipped {len(new_skill_reflections)} reflection(s) that don't map to existing skills")
                # Record skipped NEW_SKILL reflections to prevent re-detection
                for reflection in new_skill_reflections:
                    if not dry_run:
                        self._record_skipped_reflection(reflection)

            # Filter by skill if specified
            if skill_filter:
                reflections = [r for r in reflections if r.skill_name == skill_filter]
                print(f"   ✓ Filtered to skill: {skill_filter}")

            # Step 3: Show proposals and get approval
            applied_count = 0
            applied_reflections = []
            for i, reflection in enumerate(reflections, 1):
                print(f"\n{'=' * 60}")
                print(f"Reflection {i}/{len(reflections)}")
                print(f"{'=' * 60}")

                success = self._process_reflection(
                    reflection,
                    dry_run=dry_run,
                    auto_approve=auto_approve
                )

                if success:
                    applied_count += 1
                    applied_reflections.append(reflection)

            # Summary
            print(f"\n{'=' * 60}")
            print("📊 Summary")
            print(f"{'=' * 60}")
            print(f"Signals detected: {len(signals)}")
            print(f"Reflections proposed: {len(reflections)}")
            print(f"Updates applied: {applied_count}")

            if dry_run:
                print("\n⚠️  DRY RUN - No changes were made")
            else:
                # Create notification summary for next session
                self.notifications.create_summary(reflections, applied_count)
                if applied_count > 0:
                    print(f"\n💾 Summary saved for next session")

            return {
                'signals': len(signals),
                'reflections': len(reflections),
                'applied': applied_count
            }

        finally:
            self.close_db()

    def _process_reflection(self,
                            reflection: Reflection,
                            dry_run: bool,
                            auto_approve: bool) -> bool:
        """Process a single reflection"""
        # Show reflection details
        print(f"\n🎯 Skill: {reflection.skill_name}")
        print(f"📝 Signal: {reflection.signal_text}")
        print(f"🔒 Confidence: {reflection.confidence.upper()}")
        print(f"📋 What Changed: {reflection.what_changed}")
        if reflection.rationale:
            print(f"💡 Rationale: {reflection.rationale}")
        print(f"🔗 Source: {reflection.source_session}")

        # Preview update
        try:
            preview = self.updater.preview_update(reflection.skill_name, reflection)
            if 'error' in preview:
                print(f"\n❌ Error: {preview['error']}")
                return False

            print(f"\n📄 File: {preview['file_path']}")
            print(f"📦 Version: {preview['current_version']} → {preview['new_version']}")
            print(f"\n✏️  Learning Entry:")
            print("---")
            print(preview['learning_entry'])
            print("---")

        except Exception as e:
            print(f"\n❌ Error previewing update: {e}")
            return False

        # Get approval
        if dry_run:
            print("\n[DRY RUN - Would apply this update]")
            return False

        approved = False
        if auto_approve and reflection.confidence == 'high':
            approved = True
            print("\n✅ Auto-approved (high confidence)")
        else:
            response = input("\n❓ Apply this update? [y/N]: ").strip().lower()
            approved = response == 'y'

        if not approved:
            print("⏭️  Skipped")
            return False

        # Apply update
        try:
            print("\n⚙️  Applying update...")

            # Update skill file
            diff = self.updater.update_skill(reflection.skill_name, reflection)
            print("   ✓ Skill file updated")

            # Git commit
            commit_sha = self.git.commit_reflection(reflection.skill_name, reflection)
            if commit_sha:
                print(f"   ✓ Committed: {commit_sha[:8]}")
            else:
                print("   ⚠️  Git commit failed")

            # Record in database
            self._record_reflection(reflection, diff, commit_sha)
            print("   ✓ Recorded in database")

            print("\n✅ Update applied successfully!")
            return True

        except Exception as e:
            print(f"\n❌ Error applying update: {e}")
            return False

    def _record_reflection(self,
                          reflection: Reflection,
                          diff: str,
                          commit_sha: Optional[str]):
        """Record reflection in database"""
        if not self.db_conn:
            return

        try:
            cursor = self.db_conn.cursor()
            cursor.execute("""
                INSERT INTO skill_reflections (
                    skill_name, source_session, signal_type, signal_text,
                    confidence, what_changed, file_diff, git_commit, reviewed_by
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                reflection.skill_name,
                reflection.source_session,
                reflection.signal_type,
                reflection.signal_text,
                reflection.confidence,
                reflection.what_changed,
                diff,
                commit_sha,
                'user'  # Manual approval (vs. auto-approved)
            ))
            self.db_conn.commit()
        except Exception as e:
            print(f"Warning: Could not record in database: {e}")

    def _record_skipped_reflection(self, reflection: Reflection):
        """Record a skipped reflection (e.g., NEW_SKILL) to prevent re-detection"""
        if not self.db_conn:
            return

        try:
            cursor = self.db_conn.cursor()
            cursor.execute("""
                INSERT INTO skill_reflections (
                    skill_name, source_session, signal_type, signal_text,
                    confidence, what_changed, file_diff, git_commit, reviewed_by
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                reflection.skill_name,
                reflection.source_session,
                reflection.signal_type,
                reflection.signal_text,
                reflection.confidence,
                'SKIPPED: Feature already implemented or not applicable',
                None,  # No diff for skipped reflections
                None,  # No commit for skipped reflections
                'auto-skipped'  # Automatically skipped (NEW_SKILL or similar)
            ))
            self.db_conn.commit()
        except Exception as e:
            # Silently fail - not critical if we can't record skipped reflections
            pass


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Reflection Engine - Self-Improving Skills System'
    )
    parser.add_argument(
        '--session',
        help='Specific session ID to analyze'
    )
    parser.add_argument(
        '--days',
        type=int,
        default=1,
        help='Number of days to look back (default: 1)'
    )
    parser.add_argument(
        '--skill',
        help='Only update this skill'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview without applying changes'
    )
    parser.add_argument(
        '--auto-approve',
        action='store_true',
        help='Auto-approve high confidence updates'
    )

    args = parser.parse_args()

    # Run reflection
    engine = ReflectionEngine()
    result = engine.reflect(
        session_id=args.session,
        days=args.days,
        skill_filter=args.skill,
        dry_run=args.dry_run,
        auto_approve=args.auto_approve
    )

    # Exit code based on results
    if 'error' in result:
        sys.exit(1)
    sys.exit(0)


if __name__ == '__main__':
    main()
