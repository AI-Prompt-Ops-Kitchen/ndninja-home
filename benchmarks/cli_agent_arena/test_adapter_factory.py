"""Test adapter factory"""

import pytest
from adapter_factory import get_adapter, list_available_adapters, check_adapter_availability
from adapters.base import CLIAgentAdapter
from adapters.mock import MockAdapter
from adapters.kimi import KimiAdapter
from adapters.claude import ClaudeCodeAdapter
from adapters.gemini import GeminiAdapter


def test_get_adapter_mock():
    """Test getting mock adapter"""
    adapter = get_adapter("mock")
    assert isinstance(adapter, MockAdapter)
    assert isinstance(adapter, CLIAgentAdapter)


def test_get_adapter_kimi():
    """Test getting Kimi adapter"""
    adapter = get_adapter("kimi")
    assert isinstance(adapter, KimiAdapter)


def test_get_adapter_claude():
    """Test getting Claude adapter"""
    adapter = get_adapter("claude")
    assert isinstance(adapter, ClaudeCodeAdapter)


def test_get_adapter_gemini():
    """Test getting Gemini adapter"""
    adapter = get_adapter("gemini")
    assert isinstance(adapter, GeminiAdapter)


def test_get_adapter_invalid():
    """Test error for invalid adapter name"""
    with pytest.raises(ValueError, match="Unknown agent"):
        get_adapter("nonexistent")


def test_list_available_adapters():
    """Test listing available adapters"""
    adapters = list_available_adapters()

    assert "mock" in adapters
    assert "kimi" in adapters
    assert "claude" in adapters
    assert "gemini" in adapters
    assert len(adapters) == 4


def test_check_adapter_availability():
    """Test checking which adapters are available"""
    availability = check_adapter_availability()

    assert isinstance(availability, dict)
    assert "mock" in availability
    assert availability["mock"] is True  # Mock is always available
