"""
Configuration for Reflection Engine
"""

import os
from pathlib import Path

# Database Configuration
DB_HOST = os.getenv('CLAUDE_MEMORY_HOST', 'localhost')
DB_PORT = int(os.getenv('CLAUDE_MEMORY_PORT', '5432'))
DB_NAME = os.getenv('CLAUDE_MEMORY_DB', 'claude_memory')
DB_USER = os.getenv('CLAUDE_MEMORY_USER', 'claude_mcp')
DB_PASSWORD = os.getenv('CLAUDE_MEMORY_PASSWORD', 'REDACTED')

# Paths
HOME_DIR = Path.home()
SKILLS_DIR = HOME_DIR / '.claude' / 'skills'
LLM_COUNCIL_SCRIPT = HOME_DIR / 'projects' / 'llm-council' / 'run_council.sh'

# Reflection Configuration
CONFIDENCE_LEVELS = ['high', 'medium', 'low']
SIGNAL_TYPES = ['correction', 'pattern', 'preference']

# Auto-approval thresholds
AUTO_APPROVE_HIGH_CONFIDENCE = True  # Auto-approve high confidence in --auto-approve mode
AUTO_APPROVE_MEDIUM_CONFIDENCE = False
AUTO_APPROVE_LOW_CONFIDENCE = False

# Signal detection patterns
CORRECTION_PATTERNS = [
    r"actually,?\s+(.+)",
    r"no,?\s+the\s+correct\s+way\s+is\s+(.+)",
    r"instead\s+of\s+(.+?),\s+use\s+(.+)",
    r"always\s+(.+?)\s+when\s+(.+)",
    r"never\s+(.+)",
    r"from\s+now\s+on,?\s+(.+)",
    r"don't\s+(.+?),\s+(.+)",
    r"shouldn't\s+(.+)",
    r"must\s+(.+)",
]

# Minimum occurrences for pattern detection
PATTERN_MIN_OCCURRENCES = 2

# LLM Council configuration
COUNCIL_TIMEOUT = 120  # seconds
COUNCIL_MODELS = ['claude', 'gpt4', 'gemini']  # Multi-model consensus

# Git configuration
GIT_AUTHOR_NAME = "Reflection System"
GIT_AUTHOR_EMAIL = "reflect@ndninja.local"

# Logging
LOG_LEVEL = os.getenv('REFLECT_LOG_LEVEL', 'INFO')
