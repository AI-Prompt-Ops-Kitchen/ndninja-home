"""Unit tests for LLM integration.

Tests the LLM module using MockLLMClient without making real API calls.
"""

import pytest
import json
from typing import Dict, Any

from sage_mode.llm import (
    LLMClient,
    MockLLMClient,
    LLMError,
    LLMValidationError,
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
    get_schema_for_role,
    build_full_prompt,
    RESPONSE_SCHEMAS,
)
from sage_mode.agents.architect_agent import ArchitectAgent
from sage_mode.agents.backend_agent import BackendAgent
from sage_mode.agents.frontend_agent import FrontendAgent
from sage_mode.agents.security_specialist_agent import SecuritySpecialistAgent
from sage_mode.agents.dba_agent import DBAAgent
from sage_mode.agents.ui_ux_designer_agent import UIUXDesignerAgent
from sage_mode.agents.it_admin_agent import ITAdminAgent


# ============================================================================
# Schema Tests
# ============================================================================

class TestSchemas:
    """Test Pydantic schema definitions."""

    def test_decision_category_values(self):
        """All decision categories should be defined."""
        categories = [c.value for c in DecisionCategory]
        assert "architecture" in categories
        assert "security" in categories
        assert "performance" in categories

    def test_decision_model(self):
        """Decision model should validate correctly."""
        decision = Decision(
            text="Use PostgreSQL",
            rationale="ACID compliance and JSON support",
            category=DecisionCategory.DATA,
        )
        assert decision.text == "Use PostgreSQL"
        assert decision.category == DecisionCategory.DATA

    def test_base_agent_response(self):
        """BaseAgentResponse should validate all required fields."""
        response = BaseAgentResponse(
            analysis="Test analysis",
            approach="Test approach",
            decisions=[],
            concerns=["Test concern"],
            confidence=0.85,
        )
        assert response.confidence == 0.85
        assert len(response.concerns) == 1

    def test_confidence_bounds(self):
        """Confidence should be bounded 0-1."""
        with pytest.raises(Exception):  # Pydantic validation error
            BaseAgentResponse(
                analysis="Test",
                approach="Test",
                confidence=1.5,  # Invalid
            )

    def test_architect_response_fields(self):
        """ArchitectResponse should have role-specific fields."""
        response = ArchitectResponse(
            analysis="System design analysis",
            approach="Microservices approach",
            confidence=0.9,
            architecture_patterns=["MVC", "Event-driven"],
            tech_stack=["Python", "FastAPI"],
        )
        assert "MVC" in response.architecture_patterns
        assert "Python" in response.tech_stack

    def test_get_schema_for_role(self):
        """Should return correct schema for each role."""
        assert get_schema_for_role("software_architect") == ArchitectResponse
        assert get_schema_for_role("backend_developer") == BackendResponse
        assert get_schema_for_role("frontend_developer") == FrontendResponse
        assert get_schema_for_role("security_specialist") == SecurityResponse
        assert get_schema_for_role("database_administrator") == DBAResponse
        assert get_schema_for_role("ui_ux_designer") == UIUXResponse
        assert get_schema_for_role("it_administrator") == ITAdminResponse
        # Unknown role returns base
        assert get_schema_for_role("unknown") == BaseAgentResponse

    def test_all_schemas_registered(self):
        """All 7 role schemas should be registered."""
        assert len(RESPONSE_SCHEMAS) == 7


# ============================================================================
# Prompt Tests
# ============================================================================

class TestPrompts:
    """Test prompt loading and assembly."""

    def test_build_full_prompt(self):
        """Should build a complete prompt with all sections."""
        prompt = build_full_prompt(
            role="software_architect",
            role_name="Software Architect",
            feature_name="User Authentication",
            task_description="Design the authentication system",
            context={"existing_tech": ["FastAPI", "PostgreSQL"]},
            schema=ArchitectResponse,
        )

        # Should contain role-specific content
        assert "Software Architect" in prompt
        assert "system design" in prompt.lower() or "architecture" in prompt.lower()

        # Should contain task info
        assert "User Authentication" in prompt
        assert "Design the authentication system" in prompt

        # Should contain context
        assert "FastAPI" in prompt

        # Should contain schema
        assert "architecture_patterns" in prompt or "component_diagram" in prompt

    def test_prompt_includes_json_instructions(self):
        """Prompt should tell LLM to respond with JSON."""
        prompt = build_full_prompt(
            role="backend_developer",
            role_name="Backend Developer",
            feature_name="API Design",
            task_description="Create REST endpoints",
            context={},
            schema=BackendResponse,
        )

        assert "JSON" in prompt or "json" in prompt


# ============================================================================
# MockLLMClient Tests
# ============================================================================

class TestMockLLMClient:
    """Test the mock LLM client."""

    @pytest.fixture
    def mock_client(self):
        """Create a mock client for testing."""
        return MockLLMClient(default_confidence=0.85)

    @pytest.mark.asyncio
    async def test_generate_returns_valid_schema(self, mock_client):
        """generate() should return a valid schema instance."""
        response = await mock_client.generate(
            prompt="Test prompt",
            schema=ArchitectResponse,
        )

        assert isinstance(response, ArchitectResponse)
        assert response.confidence == 0.85
        assert len(response.analysis) > 0

    @pytest.mark.asyncio
    async def test_generate_tracks_calls(self, mock_client):
        """Should track call count and last prompt."""
        assert mock_client.call_count == 0

        await mock_client.generate("First prompt", ArchitectResponse)
        assert mock_client.call_count == 1
        assert mock_client.last_prompt == "First prompt"

        await mock_client.generate("Second prompt", BackendResponse)
        assert mock_client.call_count == 2
        assert mock_client.last_prompt == "Second prompt"

    @pytest.mark.asyncio
    async def test_generate_raw(self, mock_client):
        """generate_raw() should return string response."""
        response = await mock_client.generate_raw("Test prompt")

        assert isinstance(response, str)
        assert "Mock response" in response

    @pytest.mark.asyncio
    async def test_custom_response(self, mock_client):
        """Should use custom response when set."""
        custom_data = {
            "analysis": "Custom analysis",
            "approach": "Custom approach",
            "decisions": [],
            "concerns": [],
            "confidence": 0.99,
            "architecture_patterns": ["Custom Pattern"],
            "component_diagram": "",
            "tech_stack": [],
            "integration_points": [],
        }
        mock_client.set_custom_response("architect", custom_data)

        response = await mock_client.generate(
            prompt="Software architect task",
            schema=ArchitectResponse,
        )

        assert response.confidence == 0.99
        assert response.analysis == "Custom analysis"
        assert "Custom Pattern" in response.architecture_patterns

    @pytest.mark.asyncio
    async def test_all_role_schemas_generate(self, mock_client):
        """All role schemas should generate valid responses."""
        schemas = [
            ArchitectResponse,
            BackendResponse,
            FrontendResponse,
            SecurityResponse,
            DBAResponse,
            UIUXResponse,
            ITAdminResponse,
        ]

        for schema in schemas:
            response = await mock_client.generate(f"Test {schema.__name__}", schema)
            assert isinstance(response, schema)
            assert 0 <= response.confidence <= 1


# ============================================================================
# JSON Parsing Tests
# ============================================================================

class TestJsonParsing:
    """Test JSON response parsing."""

    @pytest.fixture
    def client(self):
        return MockLLMClient()

    def test_parse_clean_json(self, client):
        """Should parse clean JSON."""
        json_str = json.dumps({
            "analysis": "Test",
            "approach": "Test",
            "decisions": [],
            "concerns": [],
            "confidence": 0.5,
        })

        result = client.parse_json_response(json_str, BaseAgentResponse)
        assert result.confidence == 0.5

    def test_parse_json_in_code_block(self, client):
        """Should extract JSON from markdown code block."""
        json_str = """```json
{
    "analysis": "Extracted",
    "approach": "From code block",
    "decisions": [],
    "concerns": [],
    "confidence": 0.75
}
```"""

        result = client.parse_json_response(json_str, BaseAgentResponse)
        assert result.analysis == "Extracted"

    def test_parse_invalid_json_raises(self, client):
        """Should raise LLMValidationError for invalid JSON."""
        with pytest.raises(LLMValidationError) as exc_info:
            client.parse_json_response("not valid json", BaseAgentResponse)

        assert "Invalid JSON" in str(exc_info.value)
        assert exc_info.value.raw_response == "not valid json"

    def test_parse_schema_mismatch_raises(self, client):
        """Should raise LLMValidationError when schema doesn't match."""
        json_str = json.dumps({
            "wrong_field": "value",
        })

        with pytest.raises(LLMValidationError) as exc_info:
            client.parse_json_response(json_str, BaseAgentResponse)

        assert exc_info.value.validation_errors is not None


# ============================================================================
# Agent LLM Integration Tests
# ============================================================================

class TestAgentLLMIntegration:
    """Test agents using LLM client."""

    @pytest.fixture
    def mock_client(self):
        return MockLLMClient()

    def test_agent_accepts_llm_client(self, mock_client):
        """Agents should accept LLM client in constructor."""
        agent = ArchitectAgent(llm_client=mock_client)
        assert agent.llm_client == mock_client

    def test_agent_without_client(self):
        """Agent without client should work for mock execution."""
        agent = ArchitectAgent()
        result = agent.execute_task("Design system")
        assert result["status"] == "started"

    @pytest.mark.asyncio
    async def test_execute_task_with_llm(self, mock_client):
        """execute_task_with_llm should call LLM and return response."""
        agent = ArchitectAgent(llm_client=mock_client)
        agent.set_feature_name("Test Feature")

        response = await agent.execute_task_with_llm("Design the system architecture")

        assert isinstance(response, ArchitectResponse)
        assert mock_client.call_count == 1
        assert "architecture" in mock_client.last_prompt.lower()

    @pytest.mark.asyncio
    async def test_execute_without_client_raises(self):
        """execute_task_with_llm without client should raise ValueError."""
        agent = ArchitectAgent()  # No client

        with pytest.raises(ValueError) as exc_info:
            await agent.execute_task_with_llm("Design system")

        assert "No LLM client configured" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_all_agents_work_with_llm(self, mock_client):
        """All 7 agent types should work with LLM."""
        agents = [
            ArchitectAgent(llm_client=mock_client),
            BackendAgent(llm_client=mock_client),
            FrontendAgent(llm_client=mock_client),
            SecuritySpecialistAgent(llm_client=mock_client),
            DBAAgent(llm_client=mock_client),
            UIUXDesignerAgent(llm_client=mock_client),
            ITAdminAgent(llm_client=mock_client),
        ]

        for agent in agents:
            agent.set_feature_name("Test Feature")
            response = await agent.execute_task_with_llm("Complete your role task")

            assert isinstance(response, BaseAgentResponse)
            assert 0 <= response.confidence <= 1
            assert len(response.analysis) > 0

    def test_agent_role_key_mapping(self):
        """Each agent should map to correct LLM role key."""
        from sage_mode.agents.base_agent import ROLE_TO_LLM_KEY
        from sage_mode.models.team_simulator import AgentRole

        expected_mappings = {
            AgentRole.ARCHITECT: "software_architect",
            AgentRole.BACKEND_DEV: "backend_developer",
            AgentRole.FRONTEND_DEV: "frontend_developer",
            AgentRole.SECURITY_SPECIALIST: "security_specialist",
            AgentRole.DBA: "database_administrator",
            AgentRole.UI_UX_DESIGNER: "ui_ux_designer",
            AgentRole.IT_ADMIN: "it_administrator",
        }

        for role, expected_key in expected_mappings.items():
            assert ROLE_TO_LLM_KEY[role] == expected_key

    @pytest.mark.asyncio
    async def test_context_passed_to_prompt(self, mock_client):
        """Agent context and decisions should be in prompt."""
        from sage_mode.models.team_simulator import DecisionJournal
        from datetime import datetime

        agent = BackendAgent(llm_client=mock_client)
        agent.set_feature_name("API Feature")
        agent.set_context({"tech_stack": "FastAPI"})

        decision = DecisionJournal(
            user_id="test",
            title="Use REST",
            description="REST over GraphQL",
            category="architecture",
            decision_type="technical",
        )
        agent.add_decision(decision)

        await agent.execute_task_with_llm("Create endpoints")

        # Check prompt contains context
        prompt = mock_client.last_prompt
        assert "FastAPI" in prompt or "tech_stack" in prompt
        assert "Use REST" in prompt or "REST over GraphQL" in prompt


# ============================================================================
# Run tests
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
