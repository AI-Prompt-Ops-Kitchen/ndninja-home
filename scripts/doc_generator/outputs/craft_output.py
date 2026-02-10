"""Craft output handler - prepares documentation for Craft publishing"""
import re
import json
import os
import tempfile
from datetime import datetime
from utils.logger import setup_logger
from config import Config

logger = setup_logger('craft_output')


class CraftOutputHandler:
    """Handler for preparing documentation for Craft publishing"""

    def __init__(self):
        """Initialize handler"""
        self.staging_dir = os.path.join(tempfile.gettempdir(), 'doc_generator_craft')
        os.makedirs(self.staging_dir, exist_ok=True)

    def publish(self, content, project, doc_type):
        """
        Prepare content for Craft publishing and save to staging area

        Args:
            content: Generated markdown content
            project: Project dict with id, title, etc.
            doc_type: Documentation type (README, API, etc.)

        Returns:
            dict: Metadata for Craft publishing or None on failure
        """
        try:
            enhanced = self._enhance_markdown(content)
            title = self._generate_title(project, doc_type)

            # Save prepared content to staging area
            staging_file = os.path.join(
                self.staging_dir,
                f"{project['id']}_{doc_type}_{int(datetime.now().timestamp())}.json"
            )

            metadata = {
                'title': title,
                'content': enhanced,
                'project_id': str(project['id']),
                'project_title': project['title'],
                'doc_type': doc_type,
                'folder_id': '1',  # Work folder
                'timestamp': datetime.now().isoformat()
            }

            with open(staging_file, 'w') as f:
                json.dump(metadata, f, indent=2)

            logger.info(f"✓ Prepared for Craft: {title}")
            logger.info(f"  Staging file: {staging_file}")

            # Return staging file path as indicator for skill to publish
            return staging_file

        except Exception as e:
            logger.error(f"Craft preparation failed: {e}")
            logger.warning("Document not prepared for Craft")
            return None

    def _enhance_markdown(self, content):
        """
        Add Craft formatting (callouts, highlights)

        Args:
            content: Original markdown content

        Returns:
            str: Enhanced markdown with Craft-specific tags
        """
        enhanced = content

        # Wrap important sections in callouts
        callout_headers = [
            'Prerequisites', 'Installation', 'Setup', 'Quick Start',
            'Getting Started', 'Requirements', 'Dependencies',
            'Configuration', 'Environment'
        ]

        for header in callout_headers:
            pattern = f'(## {header}.*?)((?=##)|$)'
            replacement = r'<callout>\1</callout>\n\n'
            enhanced = re.sub(pattern, replacement, enhanced,
                            flags=re.DOTALL | re.IGNORECASE)

        # Highlight warnings (gold)
        warning_terms = [
            'breaking change', 'deprecated', 'warning',
            'important', 'API key', 'secret', 'token', 'password'
        ]
        for term in warning_terms:
            enhanced = self._highlight_term(enhanced, term, '#FFD700')

        # Highlight features (turquoise)
        feature_terms = ['new feature', 'key feature']
        for term in feature_terms:
            enhanced = self._highlight_term(enhanced, term, '#00CED1')

        return enhanced

    def _highlight_term(self, text, term, color):
        """
        Apply highlight outside code blocks

        Args:
            text: Text to highlight
            term: Term to find and highlight
            color: Hex color code

        Returns:
            str: Text with highlights applied
        """
        parts = text.split('```')
        for i in range(0, len(parts), 2):
            pattern = re.compile(re.escape(term), re.IGNORECASE)
            parts[i] = pattern.sub(
                f"<highlight color='{color}'>{term}</highlight>",
                parts[i]
            )
        return '```'.join(parts)

    def _generate_title(self, project, doc_type):
        """
        Generate timestamped title

        Args:
            project: Project dict with title
            doc_type: Documentation type

        Returns:
            str: Timestamped document title
        """
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
        return f"{doc_type}: {project['title']} - {timestamp}"
