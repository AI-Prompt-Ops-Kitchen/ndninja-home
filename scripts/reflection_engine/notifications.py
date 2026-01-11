"""
Notification System - Creates reflection summaries for next session
"""

from datetime import datetime
from pathlib import Path
from typing import List, Optional
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

    def add_attention_alert(self, attention_skills: List) -> bool:
        """
        Add attention alert to the summary if skills need attention.

        Args:
            attention_skills: List of SkillHealth objects needing attention

        Returns:
            True if alert was added, False otherwise
        """
        if not attention_skills:
            return False

        # Build alert section
        alert = "\n\n## ⚠️ Skills Needing Attention\n\n"
        alert += "_The following skills have low health scores and may need review:_\n\n"

        for skill in attention_skills[:5]:  # Limit to top 5
            score = getattr(skill, 'health_score', 0)
            reason = getattr(skill, 'attention_reason', 'Unknown reason')
            alert += f"- **{skill.skill_name}** (Score: {score:.0f}): {reason}\n"

        alert += "\n_Run `/evolution-feedback` to review and rate learnings._\n"

        # Append to existing summary or create new file
        if self.summary_file.exists():
            content = self.summary_file.read_text()
            if "Skills Needing Attention" not in content:
                content += alert
                self.summary_file.write_text(content)
        else:
            # Create minimal summary with just attention alert
            summary = f"""# 🧠 Skill Health Alert

_Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}_

{alert}
"""
            self.summary_file.write_text(summary)

        return True

    def create_summary_with_attention(self,
                                       reflections: List[Reflection],
                                       applied_count: int,
                                       attention_skills: Optional[List] = None):
        """
        Create summary with optional attention alerts.

        Args:
            reflections: List of all reflections analyzed
            applied_count: Number of reflections applied
            attention_skills: Optional list of skills needing attention
        """
        # Create base summary
        self.create_summary(reflections, applied_count)

        # Add attention alert if needed
        if attention_skills:
            self.add_attention_alert(attention_skills)
