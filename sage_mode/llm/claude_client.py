"""Claude API client implementation.

Provides the real LLM client that calls Claude's API with
retry logic and proper error handling.
"""

import os
import logging
from typing import Type, Optional

import anthropic
from anthropic import APIError, APIConnectionError, RateLimitError
from pydantic import BaseModel
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from .client import (
    LLMClient,
    LLMError,
    LLMValidationError,
    LLMRateLimitError,
    LLMConnectionError,
)


logger = logging.getLogger(__name__)


# Default model configuration
DEFAULT_MODEL = "claude-sonnet-4-20250514"
DEFAULT_MAX_RETRIES = 3


class ClaudeClient(LLMClient):
    """Claude API client with retry logic and structured output support.

    Uses Anthropic's Python SDK to communicate with Claude.
    Handles rate limiting, retries, and response validation.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = DEFAULT_MODEL,
        max_retries: int = DEFAULT_MAX_RETRIES,
    ):
        """Initialize the Claude client.

        Args:
            api_key: Anthropic API key. Falls back to ANTHROPIC_API_KEY env var.
            model: Model to use (default: claude-sonnet-4-20250514)
            max_retries: Maximum retry attempts for transient failures
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Anthropic API key required. Set ANTHROPIC_API_KEY env var "
                "or pass api_key parameter."
            )

        self.model = model
        self.max_retries = max_retries
        self._client = anthropic.Anthropic(api_key=self.api_key)

        logger.info(f"ClaudeClient initialized with model: {model}")

    def _create_retry_decorator(self):
        """Create a retry decorator with the configured settings."""
        return retry(
            stop=stop_after_attempt(self.max_retries),
            wait=wait_exponential(multiplier=1, min=1, max=60),
            retry=retry_if_exception_type((APIConnectionError, RateLimitError)),
            before_sleep=lambda retry_state: logger.warning(
                f"Retrying Claude API call (attempt {retry_state.attempt_number})"
            ),
        )

    async def generate(
        self,
        prompt: str,
        schema: Type[BaseModel],
        max_tokens: int = 4096,
        temperature: float = 0.7,
    ) -> BaseModel:
        """Generate a structured response from Claude.

        Args:
            prompt: The complete prompt to send
            schema: Pydantic model class for response validation
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature (0-1)

        Returns:
            Validated Pydantic model instance

        Raises:
            LLMValidationError: If response doesn't match schema
            LLMRateLimitError: If rate limited after retries
            LLMConnectionError: On network errors after retries
            LLMError: On other errors
        """
        # Get raw response
        raw_response = await self.generate_raw(prompt, max_tokens, temperature)

        # Parse and validate
        return self.parse_json_response(raw_response, schema)

    async def generate_raw(
        self,
        prompt: str,
        max_tokens: int = 4096,
        temperature: float = 0.7,
    ) -> str:
        """Generate a raw text response from Claude.

        Uses sync client with async wrapper since anthropic SDK's
        async client requires additional dependencies.

        Args:
            prompt: The complete prompt to send
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature (0-1)

        Returns:
            Raw text response

        Raises:
            LLMRateLimitError: If rate limited after retries
            LLMConnectionError: On network errors after retries
            LLMError: On other errors
        """
        retry_decorator = self._create_retry_decorator()

        @retry_decorator
        def _call_api():
            return self._client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[
                    {"role": "user", "content": prompt}
                ],
            )

        try:
            logger.debug(f"Calling Claude API (model: {self.model})")
            response = _call_api()

            # Extract text content
            if response.content and len(response.content) > 0:
                text_block = response.content[0]
                if hasattr(text_block, "text"):
                    result = text_block.text
                    logger.debug(
                        f"Claude response received "
                        f"(tokens: {response.usage.input_tokens} in, "
                        f"{response.usage.output_tokens} out)"
                    )
                    return result

            raise LLMError("Empty response from Claude API")

        except RateLimitError as e:
            logger.error(f"Rate limited by Claude API: {e}")
            # Try to extract retry-after header
            retry_after = getattr(e, "retry_after", None)
            raise LLMRateLimitError(
                f"Rate limited: {e}",
                retry_after=retry_after,
            )

        except APIConnectionError as e:
            logger.error(f"Connection error to Claude API: {e}")
            raise LLMConnectionError(f"Connection failed: {e}")

        except APIError as e:
            logger.error(f"Claude API error: {e}")
            raise LLMError(f"API error: {e}")

        except Exception as e:
            logger.error(f"Unexpected error calling Claude: {e}")
            raise LLMError(f"Unexpected error: {e}")


def create_client(
    use_mock: bool = False,
    api_key: Optional[str] = None,
    model: str = DEFAULT_MODEL,
) -> LLMClient:
    """Factory function to create the appropriate LLM client.

    Args:
        use_mock: If True, return MockLLMClient for testing
        api_key: Anthropic API key (only for real client)
        model: Model to use (only for real client)

    Returns:
        LLMClient instance (either MockLLMClient or ClaudeClient)
    """
    if use_mock:
        from .client import MockLLMClient
        logger.info("Creating MockLLMClient for testing")
        return MockLLMClient()

    logger.info(f"Creating ClaudeClient with model: {model}")
    return ClaudeClient(api_key=api_key, model=model)
