"""
Semantic Deduplication - Checks if suggested features already exist in codebase

This module prevents false NEW_SKILL detections by checking:
1. Skill registry (existing skill files)
2. Plugin registry (installed_plugins.json)
3. Recent reflections (fingerprint similarity)
4. Codebase grep (for implementations)
"""

import os
import json
import re
import subprocess
from pathlib import Path
from typing import List, Optional
from dataclasses import dataclass
from difflib import SequenceMatcher


@dataclass
class DedupResult:
    """Result of semantic deduplication check"""
    is_duplicate: bool
    match_type: Optional[str]  # 'skill', 'plugin', 'reflection', 'code'
    match_name: Optional[str]  # Name of matching item
    confidence: float  # 0.0 to 1.0
    reason: str


class SemanticDeduplicator:
    """
    Checks if suggested features already exist in the codebase.

    Uses multiple strategies:
    - Skill file name/description matching
    - Plugin name matching
    - Reflection fingerprint similarity
    - Codebase grep for implementations
    """

    def __init__(self,
                 skills_dir: Optional[str] = None,
                 plugins_file: Optional[str] = None,
                 codebase_dirs: Optional[List[str]] = None):
        """
        Initialize deduplicator.

        Args:
            skills_dir: Path to skills directory (default: ~/.claude/skills)
            plugins_file: Path to installed_plugins.json
            codebase_dirs: List of directories to grep for implementations
        """
        home = Path.home()
        self.skills_dir = Path(skills_dir) if skills_dir else home / '.claude' / 'skills'
        self.plugins_file = Path(plugins_file) if plugins_file else home / '.claude' / 'plugins' / 'installed_plugins.json'
        self.codebase_dirs = codebase_dirs or [
            str(home / '.claude'),
            str(home / 'projects' / 'kage-bunshin'),
            str(home / 'scripts')
        ]

        # Cache for skill names and descriptions
        self._skill_cache = None
        self._plugin_cache = None

    def check_duplicate(self,
                       signal_text: str,
                       signal_type: str = 'correction') -> DedupResult:
        """
        Check if a signal describes a feature that already exists.

        Args:
            signal_text: The signal text to check
            signal_type: Type of signal (correction, pattern, preference)

        Returns:
            DedupResult with duplicate status and details
        """
        # Extract potential feature names from signal
        feature_keywords = self._extract_feature_keywords(signal_text)

        if not feature_keywords:
            return DedupResult(
                is_duplicate=False,
                match_type=None,
                match_name=None,
                confidence=0.0,
                reason="No feature keywords detected"
            )

        # Check each strategy in order of reliability

        # 1. Check skills
        skill_match = self._check_skills(feature_keywords, signal_text)
        if skill_match and skill_match.confidence >= 0.7:
            return skill_match

        # 2. Check plugins
        plugin_match = self._check_plugins(feature_keywords, signal_text)
        if plugin_match and plugin_match.confidence >= 0.7:
            return plugin_match

        # 3. Check codebase with grep
        code_match = self._check_codebase(feature_keywords)
        if code_match and code_match.confidence >= 0.8:
            return code_match

        # Return best partial match or no match
        best_match = max(
            [skill_match, plugin_match, code_match],
            key=lambda x: x.confidence if x else 0,
            default=None
        )

        if best_match and best_match.confidence >= 0.5:
            return best_match

        return DedupResult(
            is_duplicate=False,
            match_type=None,
            match_name=None,
            confidence=0.0,
            reason="No matching features found"
        )

    def _extract_feature_keywords(self, text: str) -> List[str]:
        """Extract potential feature/skill names from signal text"""
        keywords = []

        # Look for skill-like patterns
        patterns = [
            r'/([a-z][a-z0-9-]+)',  # /skill-name
            r'skill[:\s]+([a-z][a-z0-9-]+)',  # skill: name
            r'plugin[:\s]+([a-z][a-z0-9-]+)',  # plugin: name
            r'feature[:\s]+([a-z][a-z0-9-]+)',  # feature: name
            r'command[:\s]+([a-z][a-z0-9-]+)',  # command: name
        ]

        for pattern in patterns:
            matches = re.findall(pattern, text.lower())
            keywords.extend(matches)

        # Extract quoted terms
        quoted = re.findall(r'["\']([^"\']+)["\']', text)
        for term in quoted:
            if len(term) > 2 and len(term) < 50:
                keywords.append(term.lower().replace(' ', '-'))

        # Extract capitalized terms (likely proper nouns/feature names)
        caps = re.findall(r'\b([A-Z][a-z]+(?:[A-Z][a-z]+)+)\b', text)
        for term in caps:
            # Convert CamelCase to kebab-case
            kebab = re.sub(r'(?<!^)(?=[A-Z])', '-', term).lower()
            keywords.append(kebab)

        return list(set(keywords))

    def _check_skills(self, keywords: List[str], signal_text: str) -> Optional[DedupResult]:
        """Check if any existing skill matches the keywords"""
        if self._skill_cache is None:
            self._load_skill_cache()

        best_match = None
        best_confidence = 0.0

        for skill_name, skill_info in (self._skill_cache or {}).items():
            # Check name similarity
            for keyword in keywords:
                name_similarity = self._string_similarity(keyword, skill_name)

                if name_similarity > best_confidence:
                    best_confidence = name_similarity
                    best_match = skill_name

            # Check description similarity
            description = skill_info.get('description', '')
            desc_similarity = self._string_similarity(signal_text.lower(), description.lower())

            if desc_similarity > best_confidence:
                best_confidence = desc_similarity
                best_match = skill_name

        if best_match and best_confidence >= 0.5:
            return DedupResult(
                is_duplicate=best_confidence >= 0.7,
                match_type='skill',
                match_name=best_match,
                confidence=best_confidence,
                reason=f"Similar to existing skill: {best_match}"
            )

        return None

    def _check_plugins(self, keywords: List[str], signal_text: str) -> Optional[DedupResult]:
        """Check if any installed plugin matches the keywords"""
        if self._plugin_cache is None:
            self._load_plugin_cache()

        best_match = None
        best_confidence = 0.0

        for plugin in (self._plugin_cache or []):
            plugin_name = plugin.get('name', '')

            for keyword in keywords:
                name_similarity = self._string_similarity(keyword, plugin_name)

                if name_similarity > best_confidence:
                    best_confidence = name_similarity
                    best_match = plugin_name

            # Check description
            description = plugin.get('description', '')
            desc_similarity = self._string_similarity(signal_text.lower(), description.lower())

            if desc_similarity > best_confidence:
                best_confidence = desc_similarity
                best_match = plugin_name

        if best_match and best_confidence >= 0.5:
            return DedupResult(
                is_duplicate=best_confidence >= 0.7,
                match_type='plugin',
                match_name=best_match,
                confidence=best_confidence,
                reason=f"Similar to installed plugin: {best_match}"
            )

        return None

    def _check_codebase(self, keywords: List[str]) -> Optional[DedupResult]:
        """Grep codebase for implementations matching keywords"""
        for keyword in keywords:
            if len(keyword) < 3:
                continue

            for codebase_dir in self.codebase_dirs:
                if not os.path.isdir(codebase_dir):
                    continue

                try:
                    # Use grep to find implementations
                    result = subprocess.run(
                        ['grep', '-r', '-l', '-i', keyword, codebase_dir],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )

                    if result.returncode == 0 and result.stdout.strip():
                        files = result.stdout.strip().split('\n')

                        # Filter to relevant files
                        relevant_files = [
                            f for f in files
                            if any(ext in f for ext in ['.py', '.md', '.sh', '.json'])
                            and '__pycache__' not in f
                        ]

                        if relevant_files:
                            return DedupResult(
                                is_duplicate=True,
                                match_type='code',
                                match_name=keyword,
                                confidence=0.8,
                                reason=f"Found '{keyword}' in {len(relevant_files)} file(s): {relevant_files[0]}"
                            )

                except subprocess.TimeoutExpired:
                    continue
                except Exception:
                    continue

        return None

    def _load_skill_cache(self):
        """Load skill names and descriptions from skills directory"""
        self._skill_cache = {}

        if not self.skills_dir.exists():
            return

        for skill_file in self.skills_dir.glob('*.md'):
            try:
                content = skill_file.read_text()

                # Parse frontmatter
                name = skill_file.stem
                description = ''

                if content.startswith('---'):
                    _, frontmatter, _ = content.split('---', 2)

                    for line in frontmatter.strip().split('\n'):
                        if line.startswith('name:'):
                            name = line.split(':', 1)[1].strip()
                        elif line.startswith('description:'):
                            description = line.split(':', 1)[1].strip()

                self._skill_cache[name] = {
                    'file': str(skill_file),
                    'description': description
                }

            except Exception:
                continue

    def _load_plugin_cache(self):
        """Load installed plugins from JSON file"""
        self._plugin_cache = []

        if not self.plugins_file.exists():
            return

        try:
            with open(self.plugins_file) as f:
                data = json.load(f)

            # Handle different formats
            if isinstance(data, list):
                self._plugin_cache = data
            elif isinstance(data, dict):
                self._plugin_cache = list(data.values())

        except Exception:
            pass

    def _string_similarity(self, a: str, b: str) -> float:
        """Calculate string similarity using SequenceMatcher"""
        if not a or not b:
            return 0.0
        return SequenceMatcher(None, a, b).ratio()

    def check_reflection_fingerprint(self,
                                     signal_text: str,
                                     db_conn) -> Optional[DedupResult]:
        """
        Check if a similar reflection has already been processed.

        Uses fuzzy matching on signal_text to find similar past reflections.

        Args:
            signal_text: The signal text to check
            db_conn: Database connection

        Returns:
            DedupResult if similar reflection found, None otherwise
        """
        try:
            cursor = db_conn.cursor()

            # Get recent reflections
            cursor.execute("""
                SELECT skill_name, signal_text, what_changed, applied_at
                FROM skill_reflections
                WHERE applied_at >= NOW() - INTERVAL '30 days'
                ORDER BY applied_at DESC
                LIMIT 100
            """)

            for row in cursor.fetchall():
                past_skill = row[0]
                past_signal = row[1] or ''
                past_what = row[2] or ''

                # Check similarity
                signal_sim = self._string_similarity(signal_text.lower(), past_signal.lower())
                what_sim = self._string_similarity(signal_text.lower(), past_what.lower())

                max_sim = max(signal_sim, what_sim)

                if max_sim >= 0.8:
                    return DedupResult(
                        is_duplicate=True,
                        match_type='reflection',
                        match_name=past_skill,
                        confidence=max_sim,
                        reason=f"Similar reflection already processed for skill: {past_skill}"
                    )

        except Exception:
            pass

        return None


# Singleton instance for easy access
_deduplicator = None

def get_deduplicator() -> SemanticDeduplicator:
    """Get or create singleton deduplicator instance"""
    global _deduplicator
    if _deduplicator is None:
        _deduplicator = SemanticDeduplicator()
    return _deduplicator
