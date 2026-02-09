"""Base class for CLI output parsers.

This module provides an abstract base class for extracting metrics
from CLI tool output (e.g., Claude Code, Kimi, Gemini CLI).
"""

from abc import ABC, abstractmethod
from typing import Dict, Any


class BaseOutputParser(ABC):
    """Abstract base class for parsing CLI output and extracting metrics.

    Subclasses must implement the extract_metrics method to parse
    CLI-specific output formats and return standardized metrics.
    """

    @abstractmethod
    def extract_metrics(self, stdout: str, stderr: str) -> Dict[str, Any]:
        """Extract metrics from CLI output.

        Args:
            stdout: Standard output from CLI execution
            stderr: Standard error from CLI execution

        Returns:
            Dictionary containing:
                - tokens (Dict[str, int]): Token usage with 'input' and 'output' keys
                - cost (float): Cost in USD
                - retries (int): Number of retry attempts
                - tool_calls (int): Number of tool calls made
                - error_recovered (bool): Whether errors were recovered from

        Raises:
            NotImplementedError: If subclass doesn't implement this method
        """
        pass
