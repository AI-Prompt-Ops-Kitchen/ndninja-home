"""LLM client interface and implementations.

Provides an abstract base class for LLM interactions and a mock
implementation for testing without API calls.
"""

import json
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Type, Optional

from pydantic import BaseModel, ValidationError

from .schemas import BaseAgentResponse, get_schema_for_role


logger = logging.getLogger(__name__)


class LLMError(Exception):
    """Base exception for LLM-related errors."""
    pass


class LLMValidationError(LLMError):
    """Raised when LLM response fails schema validation."""
    def __init__(self, message: str, raw_response: str, validation_errors: Any = None):
        super().__init__(message)
        self.raw_response = raw_response
        self.validation_errors = validation_errors


class LLMRateLimitError(LLMError):
    """Raised when rate limited by LLM provider."""
    def __init__(self, message: str, retry_after: Optional[float] = None):
        super().__init__(message)
        self.retry_after = retry_after


class LLMConnectionError(LLMError):
    """Raised on network/connection errors."""
    pass


class LLMClient(ABC):
    """Abstract base class for LLM clients.

    All LLM implementations must implement this interface,
    allowing easy swapping between providers (Claude, Gemini, etc.)
    and using mocks for testing.
    """

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        schema: Type[BaseModel],
        max_tokens: int = 4096,
        temperature: float = 0.7,
    ) -> BaseModel:
        """Generate a structured response from the LLM.

        Args:
            prompt: The complete prompt to send
            schema: Pydantic model class for response validation
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature (0-1)

        Returns:
            Validated Pydantic model instance

        Raises:
            LLMValidationError: If response doesn't match schema
            LLMRateLimitError: If rate limited
            LLMConnectionError: On network errors
            LLMError: On other errors
        """
        pass

    @abstractmethod
    async def generate_raw(
        self,
        prompt: str,
        max_tokens: int = 4096,
        temperature: float = 0.7,
    ) -> str:
        """Generate a raw text response without schema validation.

        Args:
            prompt: The complete prompt to send
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature (0-1)

        Returns:
            Raw text response

        Raises:
            LLMRateLimitError: If rate limited
            LLMConnectionError: On network errors
            LLMError: On other errors
        """
        pass

    def parse_json_response(self, response: str, schema: Type[BaseModel]) -> BaseModel:
        """Parse and validate a JSON response against a schema.

        Args:
            response: Raw JSON string from LLM
            schema: Pydantic model to validate against

        Returns:
            Validated Pydantic model instance

        Raises:
            LLMValidationError: If parsing or validation fails
        """
        # Try to extract JSON from response (in case of markdown code blocks)
        json_str = response.strip()
        if json_str.startswith("```"):
            # Extract from code block
            lines = json_str.split("\n")
            start = 1 if lines[0].startswith("```") else 0
            end = len(lines)
            for i, line in enumerate(lines[1:], 1):
                if line.strip() == "```":
                    end = i
                    break
            json_str = "\n".join(lines[start:end])

        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            raise LLMValidationError(
                f"Invalid JSON in response: {e}",
                raw_response=response,
                validation_errors=str(e),
            )

        try:
            return schema.model_validate(data)
        except ValidationError as e:
            raise LLMValidationError(
                f"Response doesn't match schema: {e}",
                raw_response=response,
                validation_errors=e.errors(),
            )


class MockLLMClient(LLMClient):
    """Mock LLM client for testing without API calls.

    Returns predictable responses based on role, useful for:
    - Unit tests
    - Development without API costs
    - CI/CD pipelines
    """

    def __init__(self, default_confidence: float = 0.85):
        """Initialize mock client.

        Args:
            default_confidence: Default confidence score for responses
        """
        self.default_confidence = default_confidence
        self.call_count = 0
        self.last_prompt: Optional[str] = None
        self._custom_responses: Dict[str, Dict[str, Any]] = {}

    def set_custom_response(self, role: str, response_data: Dict[str, Any]) -> None:
        """Set a custom response for a specific role.

        Args:
            role: Agent role key
            response_data: Dict to return for this role
        """
        self._custom_responses[role] = response_data

    def _generate_mock_response(self, schema: Type[BaseModel]) -> Dict[str, Any]:
        """Generate a mock response matching the schema."""
        # Base fields present in all responses
        response = {
            "analysis": "Mock analysis: This is a simulated response for testing purposes.",
            "approach": "Mock approach: Would follow standard practices for this task.",
            "decisions": [
                {
                    "text": "Use established patterns",
                    "rationale": "Consistency and maintainability",
                    "category": "architecture",
                }
            ],
            "concerns": ["This is a mock response - not for production use"],
            "confidence": self.default_confidence,
        }

        # Add role-specific fields based on schema name
        schema_name = schema.__name__

        if schema_name == "ArchitectResponse":
            response.update({
                "architecture_patterns": ["MVC", "Repository Pattern"],
                "component_diagram": "Mock diagram placeholder",
                "tech_stack": ["Python", "FastAPI", "PostgreSQL"],
                "integration_points": ["External API"],
            })
        elif schema_name == "BackendResponse":
            response.update({
                "endpoints": [{"method": "GET", "path": "/api/test", "description": "Mock endpoint"}],
                "data_models": [{"name": "MockModel", "fields": ["id", "name"]}],
                "code_snippets": [],
                "performance_notes": ["Consider caching"],
            })
        elif schema_name == "FrontendResponse":
            response.update({
                "components": [{"name": "MockComponent", "type": "functional"}],
                "state_management": "React Context",
                "code_snippets": [],
                "accessibility_notes": ["Add ARIA labels"],
            })
        elif schema_name == "SecurityResponse":
            response.update({
                "vulnerabilities": [],
                "risk_level": "low",
                "mitigations": ["Input validation", "Rate limiting"],
                "compliance_notes": ["GDPR consideration needed"],
            })
        elif schema_name == "DBAResponse":
            response.update({
                "schema_changes": [],
                "indexes": ["idx_mock_id"],
                "queries": [],
                "migration_steps": ["Create table", "Add index"],
            })
        elif schema_name == "UIUXResponse":
            response.update({
                "user_flows": ["User enters data", "System validates", "Success message"],
                "wireframe_description": "Simple form layout",
                "design_tokens": {"primary_color": "#007AFF", "spacing": "8px"},
                "accessibility_score": 0.9,
            })
        elif schema_name == "ITAdminResponse":
            response.update({
                "infrastructure": [{"type": "container", "name": "app"}],
                "deployment_steps": ["Build image", "Deploy to cluster"],
                "monitoring_config": {"alerts": ["high_cpu", "error_rate"]},
                "scaling_notes": ["Horizontal scaling recommended"],
            })

        return response

    async def generate(
        self,
        prompt: str,
        schema: Type[BaseModel],
        max_tokens: int = 4096,
        temperature: float = 0.7,
    ) -> BaseModel:
        """Generate a mock structured response.

        Args:
            prompt: The prompt (stored for inspection)
            schema: Pydantic model for the response
            max_tokens: Ignored in mock
            temperature: Ignored in mock

        Returns:
            Mock response matching the schema
        """
        self.call_count += 1
        self.last_prompt = prompt

        logger.debug(f"MockLLMClient.generate called (call #{self.call_count})")

        # Check for custom response
        for role, custom_data in self._custom_responses.items():
            if role in prompt.lower():
                return schema.model_validate(custom_data)

        # Generate mock response
        response_data = self._generate_mock_response(schema)
        return schema.model_validate(response_data)

    async def generate_raw(
        self,
        prompt: str,
        max_tokens: int = 4096,
        temperature: float = 0.7,
    ) -> str:
        """Generate a raw mock response.

        Args:
            prompt: The prompt
            max_tokens: Ignored in mock
            temperature: Ignored in mock

        Returns:
            Mock text response
        """
        self.call_count += 1
        self.last_prompt = prompt

        logger.debug(f"MockLLMClient.generate_raw called (call #{self.call_count})")

        return f"Mock response to prompt (length: {len(prompt)} chars)"
