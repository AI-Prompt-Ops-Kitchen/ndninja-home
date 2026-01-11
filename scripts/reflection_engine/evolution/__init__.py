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

__all__ = [
    'HealthCalculator',
    'EvolutionReport',
    'FeedbackCollector',
    'EventTracker',
    'UsageTracker',
    'track_session_usage',
]

__version__ = '1.0.0'
