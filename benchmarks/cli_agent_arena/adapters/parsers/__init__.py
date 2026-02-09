"""Output parsers for CLI tools.

This package provides parsers for extracting metrics from various
CLI agent outputs (Claude Code, Kimi, Gemini CLI, etc.).
"""

from .base_parser import BaseOutputParser
from .kimi_parser import KimiParser
from .claude_parser import ClaudeParser
from .gemini_parser import GeminiParser

__all__ = ["BaseOutputParser", "KimiParser", "ClaudeParser", "GeminiParser"]
