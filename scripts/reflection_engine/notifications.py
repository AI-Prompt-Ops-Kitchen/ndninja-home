"""
Notification System - Creates reflection summaries for next session
"""

from datetime import datetime
from pathlib import Path
from typing import List
from analyzer import Reflection


class NotificationManager:
    """Manages reflection notifications for user"""

    def __init__(self, summary_file: Path):
        self.summary_file = summary_file

    def create_summary(self, reflections: List[Reflection], applied_count: int):
        """
        Create a summary of applied reflections for next session.

        Args:
            reflections: List of all reflections analyzed
            applied_count: Number of reflections that were applied
        """
        if applied_count == 0:
            # No reflections applied, don't create summary
            if self.summary_file.exists():
                self.summary_file.unlink()
            return

        # Group reflections by skill
        by_skill = {}
        for r in reflections:
            if r.skill_name not in by_skill:
                by_skill[r.skill_name] = []
            by_skill[r.skill_name].append(r)

        # Build summary
        summary = f"""# 🧠 I Learned Something New!

_Reflections applied automatically after your last session ({datetime.now().strftime('%Y-%m-%d %H:%M')})_

## Skills Improved ({len(by_skill)})

"""

        for skill_name, skill_reflections in by_skill.items():
            summary += f"### {skill_name}\n\n"
            for refl in skill_reflections:
                summary += f"- **{refl.signal_text[:80]}...**\n"
                summary += f"  - Confidence: {refl.confidence.title()}\n"
                summary += f"  - {refl.what_changed}\n\n"

        summary += f"""---

_Total: {applied_count} reflection(s) applied_

These learnings are now permanent parts of the skills and will inform better recommendations going forward.

**View details:** `tail -100 /tmp/reflection-auto-$(date +%Y%m%d).log`

**See all reflections:** Query skill_reflections table in workspace database
"""

        # Write summary
        self.summary_file.write_text(summary)

    def has_summary(self) -> bool:
        """Check if a summary exists"""
        return self.summary_file.exists()

    def get_summary(self) -> str:
        """Get the summary content"""
        if not self.summary_file.exists():
            return ""
        return self.summary_file.read_text()

    def clear_summary(self):
        """Clear the summary file"""
        if self.summary_file.exists():
            self.summary_file.unlink()
