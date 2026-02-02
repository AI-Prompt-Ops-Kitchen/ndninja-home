"""Adapter factory for creating CLI agent adapters"""

from typing import Dict, Type
from adapters.base import CLIAgentAdapter
from adapters.mock import MockAdapter
from adapters.kimi import KimiAdapter
from adapters.claude import ClaudeCodeAdapter
from adapters.gemini import GeminiAdapter


# Registry of available adapters
ADAPTERS: Dict[str, Type[CLIAgentAdapter]] = {
    "mock": MockAdapter,
    "kimi": KimiAdapter,
    "claude": ClaudeCodeAdapter,
    "gemini": GeminiAdapter,
}


def get_adapter(agent_name: str, **kwargs) -> CLIAgentAdapter:
    """Get adapter instance by agent name

    Args:
        agent_name: Name of agent (mock, kimi, claude, gemini)
        **kwargs: Additional arguments to pass to adapter constructor

    Returns:
        Adapter instance

    Raises:
        ValueError: If agent_name is not recognized
    """
    if agent_name not in ADAPTERS:
        available = ", ".join(ADAPTERS.keys())
        raise ValueError(
            f"Unknown agent: {agent_name}. "
            f"Available agents: {available}"
        )

    adapter_class = ADAPTERS[agent_name]
    return adapter_class(**kwargs)


def list_available_adapters() -> list[str]:
    """List all available adapter names

    Returns:
        List of adapter names
    """
    return list(ADAPTERS.keys())


def check_adapter_availability() -> Dict[str, bool]:
    """Check which adapters are actually available (CLI installed)

    Returns:
        Dict mapping agent name to availability status
    """
    availability = {}

    for name, adapter_class in ADAPTERS.items():
        if name == "mock":
            availability[name] = True
        elif hasattr(adapter_class, "check_available"):
            availability[name] = adapter_class.check_available()
        else:
            availability[name] = False

    return availability
