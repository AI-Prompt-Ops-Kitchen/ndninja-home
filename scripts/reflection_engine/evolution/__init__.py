"""
Evolution Dashboard Module

Phase 3 of the Self-Improving Skills System.
Provides visibility into skill health, learning effectiveness,
and evolution over time.
"""

from .health import HealthCalculator
from .report import EvolutionReport
from .feedback import FeedbackCollector
from .tracker import EventTracker
from .usage import UsageTracker, track_session_usage
from .digest import DigestGenerator, generate_and_save_digest
from .automation import (
    generate_weekly_digest,
    check_attention_needed,
    get_evolution_summary,
    run_weekly_automation
)

__all__ = [
    'HealthCalculator',
    'EvolutionReport',
    'FeedbackCollector',
    'EventTracker',
    'UsageTracker',
    'track_session_usage',
    'DigestGenerator',
    'generate_and_save_digest',
    'generate_weekly_digest',
    'check_attention_needed',
    'get_evolution_summary',
    'run_weekly_automation',
]

__version__ = '1.0.0'
