"""Integration tests using real Claude API.

These tests make actual API calls and cost money.
They are skipped by default unless ANTHROPIC_API_KEY is set.

Run with: ANTHROPIC_API_KEY=your-key pytest tests/test_llm_integration_real.py -v
"""

import os
import pytest

from sage_mode.llm import (
    ClaudeClient,
    create_client,
    ArchitectResponse,
    BackendResponse,
    SecurityResponse,
)
from sage_mode.agents.architect_agent import ArchitectAgent
from sage_mode.agents.backend_agent import BackendAgent


# Skip all tests if no API key
pytestmark = pytest.mark.skipif(
    not os.getenv("ANTHROPIC_API_KEY"),
    reason="ANTHROPIC_API_KEY not set - skipping real API tests"
)


# ============================================================================
# ClaudeClient Tests
# ============================================================================

class TestClaudeClient:
    """Test real Claude API calls."""

    @pytest.fixture
    def client(self):
        """Create real Claude client."""
        return ClaudeClient()

    @pytest.mark.asyncio
    async def test_generate_raw_response(self, client):
        """Should get raw text response from Claude."""
        response = await client.generate_raw(
            prompt="Respond with exactly: HELLO SAGE MODE",
            max_tokens=50,
        )

        assert "HELLO" in response.upper() or "SAGE" in response.upper()

    @pytest.mark.asyncio
    async def test_generate_structured_response(self, client):
        """Should get structured JSON response matching schema."""
        prompt = """You are a software architect. Analyze adding user authentication.

Respond with ONLY valid JSON matching this schema:
{
    "analysis": "string - your analysis",
    "approach": "string - your approach",
    "decisions": [],
    "concerns": [],
    "confidence": 0.85,
    "architecture_patterns": ["list of patterns"],
    "component_diagram": "",
    "tech_stack": ["list of tech"],
    "integration_points": []
}"""

        response = await client.generate(
            prompt=prompt,
            schema=ArchitectResponse,
            max_tokens=1000,
        )

        assert isinstance(response, ArchitectResponse)
        assert len(response.analysis) > 10
        assert 0 <= response.confidence <= 1

    @pytest.mark.asyncio
    async def test_backend_schema_response(self, client):
        """Should generate valid BackendResponse."""
        prompt = """You are a backend developer. Design a REST endpoint for user registration.

Respond with ONLY valid JSON matching this schema:
{
    "analysis": "string",
    "approach": "string",
    "decisions": [],
    "concerns": [],
    "confidence": 0.8,
    "endpoints": [{"method": "POST", "path": "/api/users", "description": "Create user"}],
    "data_models": [],
    "code_snippets": [],
    "performance_notes": []
}"""

        response = await client.generate(
            prompt=prompt,
            schema=BackendResponse,
            max_tokens=1000,
        )

        assert isinstance(response, BackendResponse)
        assert len(response.endpoints) > 0


# ============================================================================
# Agent Integration Tests
# ============================================================================

class TestAgentRealLLM:
    """Test agents with real Claude API."""

    @pytest.fixture
    def claude_client(self):
        return ClaudeClient()

    @pytest.mark.asyncio
    async def test_architect_agent_real_llm(self, claude_client):
        """ArchitectAgent should produce real analysis."""
        agent = ArchitectAgent(llm_client=claude_client)
        agent.set_feature_name("E-commerce Checkout")

        response = await agent.execute_task_with_llm(
            "Design the architecture for a checkout flow with cart, "
            "payment processing, and order confirmation."
        )

        assert isinstance(response, ArchitectResponse)
        assert len(response.analysis) > 50  # Real response has substance
        assert response.confidence > 0

        # Real architect should suggest patterns or tech
        has_content = (
            len(response.architecture_patterns) > 0 or
            len(response.tech_stack) > 0 or
            len(response.decisions) > 0
        )
        assert has_content, "Real response should have architectural content"

    @pytest.mark.asyncio
    async def test_backend_agent_real_llm(self, claude_client):
        """BackendAgent should produce real API design."""
        agent = BackendAgent(llm_client=claude_client)
        agent.set_feature_name("User API")

        response = await agent.execute_task_with_llm(
            "Design REST endpoints for user registration and login"
        )

        assert isinstance(response, BackendResponse)
        assert len(response.analysis) > 20

        # Real backend dev should suggest endpoints
        if len(response.endpoints) > 0:
            endpoint = response.endpoints[0]
            assert "method" in endpoint or "path" in endpoint


# ============================================================================
# Factory Function Tests
# ============================================================================

class TestClientFactory:
    """Test create_client factory function."""

    def test_create_mock_client(self):
        """Should create mock client when use_mock=True."""
        from sage_mode.llm import MockLLMClient

        client = create_client(use_mock=True)
        assert isinstance(client, MockLLMClient)

    def test_create_real_client(self):
        """Should create Claude client when use_mock=False."""
        client = create_client(use_mock=False)
        assert isinstance(client, ClaudeClient)

    def test_client_model_configuration(self):
        """Should use specified model."""
        client = ClaudeClient(model="claude-sonnet-4-20250514")
        assert client.model == "claude-sonnet-4-20250514"


# ============================================================================
# Cost Awareness Test
# ============================================================================

class TestCostAwareness:
    """Tests to help track API costs."""

    @pytest.mark.asyncio
    async def test_minimal_token_request(self):
        """Verify we can make small requests to minimize test costs."""
        client = ClaudeClient()

        # Very small request
        response = await client.generate_raw(
            prompt="Say: OK",
            max_tokens=10,
        )

        assert len(response) < 50  # Response should be small


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
