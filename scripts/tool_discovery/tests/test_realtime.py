"""
Unit tests for real-time keyword detection.

Tests the RealtimeDiscovery class that scans user prompts for tool keywords
and suggests relevant tools with rate limiting.
"""

import os
import pytest
import json
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from realtime import RealtimeDiscovery


@pytest.fixture
def discovery():
    """Create a fresh RealtimeDiscovery instance for each test."""
    disc = RealtimeDiscovery()
    yield disc
    # Cleanup after test
    disc.reset()
    disc.close()  # Close database connection to prevent resource leak


class TestRealtimeDiscovery:
    """Test suite for RealtimeDiscovery."""

    def test_keyword_matching_exact(self, discovery):
        """Test exact keyword pattern matching."""
        # Test llm-council keywords
        prompt1 = "I need multi-model consensus for this decision"
        match1 = discovery.match_keywords(prompt1)
        assert match1 is not None
        assert match1['tool_name'] == 'llm-council'

        # Test kage-bunshin keywords
        prompt2 = "Can you use the distributed system with 72b model?"
        match2 = discovery.match_keywords(prompt2)
        assert match2 is not None
        assert match2['tool_name'] == 'kage-bunshin'

        # Test docker-env-debugger keywords
        prompt3 = "I'm having issues with my docker environment"
        match3 = discovery.match_keywords(prompt3)
        assert match3 is not None
        assert match3['tool_name'] == 'docker-env-debugger'

        # Test case insensitivity
        prompt4 = "MULTI-MODEL analysis needed"
        match4 = discovery.match_keywords(prompt4)
        assert match4 is not None
        assert match4['tool_name'] == 'llm-council'

    def test_keyword_matching_none(self, discovery):
        """Test that non-matching prompts return None."""
        # No keyword matches
        prompt1 = "What is the weather today?"
        match1 = discovery.match_keywords(prompt1)
        assert match1 is None

        # Partial words that shouldn't match
        prompt2 = "I like multiplayer games"
        match2 = discovery.match_keywords(prompt2)
        assert match2 is None

        # Empty prompt
        prompt3 = ""
        match3 = discovery.match_keywords(prompt3)
        assert match3 is None

    def test_rate_limit_check(self, discovery):
        """Test rate limiting logic."""
        # First 5 messages should allow suggestions
        for i in range(5):
            allowed = discovery.check_rate_limit()
            assert allowed is True, f"Message {i+1} should be allowed"
            # Simulate message processed
            discovery.state['message_count'] += 1

        # 6th message should be rate-limited
        allowed = discovery.check_rate_limit()
        assert allowed is False, "6th message should be rate-limited"

        # Reset counter (simulate suggestion shown)
        discovery.state['message_count'] = 0
        discovery._save_state()

        # After reset, should allow again
        allowed = discovery.check_rate_limit()
        assert allowed is True, "After reset, should allow suggestions"

    def test_format_suggestion(self, discovery):
        """Test suggestion formatting."""
        # Mock tool data
        tool_data = {
            'tool_name': 'llm-council',
            'command': '/llm-council',
            'description': 'Multi-model consensus analysis',
            'keywords': ['multi-model', 'consensus']
        }

        formatted = discovery.format_suggestion(tool_data)

        # Check for key components
        assert '💡' in formatted, "Should have lightbulb emoji indicator"
        assert 'llm-council' in formatted, "Should contain tool name"
        assert '/llm-council' in formatted, "Should contain command"
        assert 'Multi-model consensus analysis' in formatted, "Should contain description"

        # Check format is reasonably structured
        assert len(formatted) > 50, "Should be a substantial suggestion"
        lines = formatted.strip().split('\n')
        assert len(lines) >= 2, "Should be multi-line"


# Run tests with pytest
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
