"""File output handler - saves documentation to local markdown files"""
import os
from datetime import datetime
from pathlib import Path
from config import Config


class FileOutputHandler:
    """Handler for saving documentation to local files"""

    def __init__(self):
        """Initialize file output handler"""
        self.output_dir = Config.DOCS_OUTPUT_DIR
        self._ensure_output_dir()

    def _ensure_output_dir(self):
        """Create output directory if it doesn't exist"""
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)

    def save(self, content, project, doc_type):
        """
        Save documentation to local file

        Args:
            content: Markdown content to save
            project: Project dict
            doc_type: Documentation type (README, API, etc.)

        Returns:
            str: Path to saved file
        """
        # Create filename
        project_slug = self._slugify(project['title'])
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{doc_type.lower()}_{project_slug}_{timestamp}.md"

        filepath = os.path.join(self.output_dir, filename)

        # Write file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

        return filepath

    def _slugify(self, text):
        """Convert text to filesystem-safe slug"""
        # Convert to lowercase and replace spaces with hyphens
        slug = text.lower().replace(' ', '-')

        # Remove special characters
        slug = ''.join(c for c in slug if c.isalnum() or c == '-')

        # Remove consecutive hyphens
        while '--' in slug:
            slug = slug.replace('--', '-')

        # Trim hyphens from ends
        slug = slug.strip('-')

        # Limit length
        return slug[:50]
