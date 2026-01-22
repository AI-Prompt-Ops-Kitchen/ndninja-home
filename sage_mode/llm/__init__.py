"""LLM integration module for Sage Mode agents.

Provides structured LLM interactions with:
- Abstract client interface for provider flexibility
- Claude API implementation with retry logic
- Mock client for testing
- Role-specific response schemas
- Prompt assembly utilities
"""

from .client import (
    LLMClient,
    LLMError,
    LLMValidationError,
    LLMRateLimitError,
    LLMConnectionError,
    MockLLMClient,
)
from .claude_client import ClaudeClient, create_client
from .schemas import (
    BaseAgentResponse,
    ArchitectResponse,
    BackendResponse,
    FrontendResponse,
    SecurityResponse,
    DBAResponse,
    UIUXResponse,
    ITAdminResponse,
    Decision,
    DecisionCategory,
    CodeSnippet,
    get_schema_for_role,
    RESPONSE_SCHEMAS,
)
from .prompts import build_full_prompt, get_role_prompt, get_base_prompt


__all__ = [
    # Client classes
    "LLMClient",
    "ClaudeClient",
    "MockLLMClient",
    "create_client",
    # Exceptions
    "LLMError",
    "LLMValidationError",
    "LLMRateLimitError",
    "LLMConnectionError",
    # Response schemas
    "BaseAgentResponse",
    "ArchitectResponse",
    "BackendResponse",
    "FrontendResponse",
    "SecurityResponse",
    "DBAResponse",
    "UIUXResponse",
    "ITAdminResponse",
    "Decision",
    "DecisionCategory",
    "CodeSnippet",
    "get_schema_for_role",
    "RESPONSE_SCHEMAS",
    # Prompt utilities
    "build_full_prompt",
    "get_role_prompt",
    "get_base_prompt",
]
