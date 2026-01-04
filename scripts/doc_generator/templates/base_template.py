"""Base template class for documentation generation"""
from abc import ABC, abstractmethod


class BaseTemplate(ABC):
    """Abstract base class for documentation templates"""

    @property
    @abstractmethod
    def required_sources(self):
        """
        List of required data sources for this template

        Returns:
            list: Source names ('db', 'git', 'memory', 'user')
        """
        pass

    @property
    @abstractmethod
    def system_prompt(self):
        """
        System prompt for Claude API

        Returns:
            str: System prompt defining documentation style and requirements
        """
        pass

    @abstractmethod
    def build_prompt(self, project, data):
        """
        Build user prompt from project and gathered data

        Args:
            project: Project dict from workspace.items
            data: Dict of gathered data from all sources

        Returns:
            str: Complete user prompt for Claude API
        """
        pass

    def post_process(self, content, data):
        """
        Post-process generated content (optional)

        Args:
            content: Generated markdown content
            data: Dict of gathered data

        Returns:
            str: Post-processed content
        """
        return content
