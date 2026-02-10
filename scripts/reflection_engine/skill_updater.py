"""
Skill Updater - Updates skill markdown files with reflection learnings
"""

import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Tuple
from analyzer import Reflection
from config import SKILLS_DIR


class SkillUpdater:
    """Updates skill markdown files with reflection learnings"""

    def __init__(self):
        self.skills_dir = SKILLS_DIR

    def update_skill(self, skill_name: str, reflection: Reflection) -> str:
        """
        Updates a skill markdown file with reflection learning.

        Args:
            skill_name: Name of the skill to update
            reflection: Reflection object with update details

        Returns:
            Git diff of the change (as string)

        Raises:
            FileNotFoundError: If skill file doesn't exist
        """
        skill_path = self.skills_dir / f"{skill_name}.md"

        if not skill_path.exists():
            raise FileNotFoundError(f"Skill file not found: {skill_path}")

        # Read current skill file
        with open(skill_path, 'r', encoding='utf-8') as f:
            original_content = f.read()

        # Parse frontmatter and body
        frontmatter, body = self._parse_frontmatter(original_content)

        # Update frontmatter metadata
        frontmatter = self._update_frontmatter(frontmatter)

        # Add to Learnings section
        body = self._add_learning(body, reflection)

        # Reconstruct file
        updated_content = self._build_file(frontmatter, body)

        # Write back
        with open(skill_path, 'w', encoding='utf-8') as f:
            f.write(updated_content)

        # Generate diff (simple version - compare before/after)
        diff = self._generate_diff(original_content, updated_content, skill_name)

        return diff

    def _parse_frontmatter(self, content: str) -> Tuple[Dict, str]:
        """
        Parse YAML frontmatter and markdown body.

        Args:
            content: Full file content

        Returns:
            Tuple of (frontmatter_dict, body_string)
        """
        # Match frontmatter between --- markers
        match = re.match(r'^---\s*\n(.*?)\n---\s*\n(.*)', content, re.DOTALL)

        if not match:
            # No frontmatter
            return {}, content

        frontmatter_text = match.group(1)
        body = match.group(2)

        # Simple YAML parsing (basic key: value pairs)
        frontmatter = {}
        for line in frontmatter_text.split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                frontmatter[key.strip()] = value.strip()

        return frontmatter, body

    def _update_frontmatter(self, frontmatter: Dict) -> Dict:
        """Update frontmatter with reflection metadata"""
        # Update version
        current_version = frontmatter.get('version', '1.0.0')
        frontmatter['version'] = self._bump_version(current_version)

        # Update last_reflection timestamp
        frontmatter['last_reflection'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Increment reflection_count
        current_count = int(frontmatter.get('reflection_count', 0))
        frontmatter['reflection_count'] = str(current_count + 1)

        return frontmatter

    def _bump_version(self, version: str) -> str:
        """Bump patch version number"""
        try:
            parts = version.split('.')
            if len(parts) >= 3:
                parts[2] = str(int(parts[2]) + 1)
            else:
                parts.append('1')
            return '.'.join(parts[:3])
        except (ValueError, IndexError):
            return '1.0.1'

    def _add_learning(self, body: str, reflection: Reflection) -> str:
        """Add learning entry to the skill body"""
        # Create learning entry
        learning_entry = self._format_learning(reflection)

        # Check if Learnings section exists
        learnings_pattern = r'(#{1,2}\s+🧠\s+Learnings.*?)(\n#{1,2}\s+|\Z)'
        match = re.search(learnings_pattern, body, re.DOTALL | re.IGNORECASE)

        if match:
            # Insert at the beginning of existing Learnings section
            existing_section = match.group(1)
            # Find where content starts (after the heading)
            heading_end = existing_section.find('\n')
            if heading_end != -1:
                updated_section = (existing_section[:heading_end + 1] +
                                   '\n' + learning_entry + '\n' +
                                   existing_section[heading_end + 1:])
            else:
                updated_section = existing_section + '\n\n' + learning_entry

            body = body[:match.start()] + updated_section + match.group(2) + body[match.end():]
        else:
            # Create new Learnings section at the end
            learnings_section = f"\n\n---\n\n## 🧠 Learnings (Auto-Updated)\n\n{learning_entry}\n"
            body = body.rstrip() + learnings_section

        return body

    def _format_learning(self, reflection: Reflection) -> str:
        """Format a learning entry in markdown"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
        signal_type_display = reflection.signal_type.title()

        entry = f"""### {timestamp} - {signal_type_display}
**Signal:** "{reflection.signal_text}"
**What Changed:** {reflection.what_changed}
**Confidence:** {reflection.confidence.title()}
**Source:** {reflection.source_session}"""

        if reflection.rationale:
            entry += f"\n**Rationale:** {reflection.rationale}"

        return entry

    def _build_file(self, frontmatter: Dict, body: str) -> str:
        """Reconstruct markdown file from frontmatter and body"""
        # Build frontmatter section
        frontmatter_lines = ['---']
        for key, value in frontmatter.items():
            frontmatter_lines.append(f"{key}: {value}")
        frontmatter_lines.append('---')

        return '\n'.join(frontmatter_lines) + '\n' + body

    def _generate_diff(self, original: str, updated: str, skill_name: str) -> str:
        """Generate a simple diff representation"""
        # Count changes
        original_lines = original.split('\n')
        updated_lines = updated.split('\n')

        added_lines = len(updated_lines) - len(original_lines)

        diff = f"""--- a/.claude/skills/{skill_name}.md
+++ b/.claude/skills/{skill_name}.md
@@ Lines changed: +{added_lines} @@

Changes:
- Updated version and reflection metadata
- Added new learning entry
- Total lines: {len(original_lines)} -> {len(updated_lines)}
"""

        return diff

    def preview_update(self, skill_name: str, reflection: Reflection) -> Dict:
        """
        Preview what would be updated without actually changing the file.

        Args:
            skill_name: Name of the skill
            reflection: Reflection to apply

        Returns:
            Dict with preview information
        """
        skill_path = self.skills_dir / f"{skill_name}.md"

        if not skill_path.exists():
            return {
                'error': f"Skill file not found: {skill_path}",
                'skill_name': skill_name
            }

        with open(skill_path, 'r', encoding='utf-8') as f:
            content = f.read()

        frontmatter, body = self._parse_frontmatter(content)
        updated_frontmatter = self._update_frontmatter(frontmatter)
        learning_entry = self._format_learning(reflection)

        return {
            'skill_name': skill_name,
            'current_version': frontmatter.get('version', '1.0.0'),
            'new_version': updated_frontmatter.get('version'),
            'learning_entry': learning_entry,
            'file_path': str(skill_path)
        }
