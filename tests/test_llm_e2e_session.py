"""End-to-end session test for LLM integration.

Demonstrates a complete session flow where all 7 agents
analyze a feature using the LLM (mock client for CI).
"""

import pytest
import asyncio

from sage_mode.llm import (
    MockLLMClient,
    create_client,
    BaseAgentResponse,
    ArchitectResponse,
    BackendResponse,
    FrontendResponse,
    SecurityResponse,
    DBAResponse,
    UIUXResponse,
    ITAdminResponse,
)
from sage_mode.agents.architect_agent import ArchitectAgent
from sage_mode.agents.backend_agent import BackendAgent
from sage_mode.agents.frontend_agent import FrontendAgent
from sage_mode.agents.security_specialist_agent import SecuritySpecialistAgent
from sage_mode.agents.dba_agent import DBAAgent
from sage_mode.agents.ui_ux_designer_agent import UIUXDesignerAgent
from sage_mode.agents.it_admin_agent import ITAdminAgent
from sage_mode.models.team_simulator import DecisionJournal


class TestE2ESession:
    """End-to-end test of a complete team session."""

    @pytest.fixture
    def llm_client(self):
        """Create mock LLM client."""
        return MockLLMClient(default_confidence=0.85)

    @pytest.fixture
    def team(self, llm_client):
        """Create full team of agents with LLM client."""
        return {
            "architect": ArchitectAgent(llm_client=llm_client),
            "backend": BackendAgent(llm_client=llm_client),
            "frontend": FrontendAgent(llm_client=llm_client),
            "security": SecuritySpecialistAgent(llm_client=llm_client),
            "dba": DBAAgent(llm_client=llm_client),
            "uiux": UIUXDesignerAgent(llm_client=llm_client),
            "itadmin": ITAdminAgent(llm_client=llm_client),
        }

    @pytest.mark.asyncio
    async def test_full_session_flow(self, team, llm_client):
        """Test complete session with all agents analyzing a feature."""
        feature_name = "User Authentication System"

        # Set feature name for all agents
        for agent in team.values():
            agent.set_feature_name(feature_name)

        # =====================================================================
        # Phase 1: Architecture Design (Architect leads)
        # =====================================================================
        architect_response = await team["architect"].execute_task_with_llm(
            "Design the high-level architecture for user authentication "
            "including login, registration, password reset, and session management."
        )

        assert isinstance(architect_response, ArchitectResponse)
        assert architect_response.confidence > 0

        # Share architect's decisions with the team
        architect_decision = DecisionJournal(
            user_id="session-test",
            title="Authentication Architecture",
            description=architect_response.approach,
            category="architecture",
            decision_type="strategic",
        )

        for agent in team.values():
            if agent != team["architect"]:
                agent.add_decision(architect_decision)

        # =====================================================================
        # Phase 2: Parallel Role Analysis
        # =====================================================================

        # All agents can work in parallel on their domain analysis
        tasks = [
            team["backend"].execute_task_with_llm(
                "Design the API endpoints for authentication: "
                "POST /auth/login, POST /auth/register, POST /auth/reset-password, "
                "GET /auth/me, POST /auth/logout"
            ),
            team["frontend"].execute_task_with_llm(
                "Design React components for: LoginForm, RegisterForm, "
                "PasswordResetForm, UserProfile, and authentication state management"
            ),
            team["security"].execute_task_with_llm(
                "Review the authentication design for security vulnerabilities. "
                "Check for OWASP Top 10 issues, session security, password handling."
            ),
            team["dba"].execute_task_with_llm(
                "Design the database schema for users, sessions, and password "
                "reset tokens. Include indexes for common queries."
            ),
            team["uiux"].execute_task_with_llm(
                "Design the user flows for login, registration, and password reset. "
                "Include error states and accessibility considerations."
            ),
            team["itadmin"].execute_task_with_llm(
                "Plan the deployment and infrastructure for authentication services. "
                "Include rate limiting, logging, and monitoring."
            ),
        ]

        results = await asyncio.gather(*tasks)

        # Verify all agents produced valid responses
        expected_types = [
            BackendResponse,
            FrontendResponse,
            SecurityResponse,
            DBAResponse,
            UIUXResponse,
            ITAdminResponse,
        ]

        for result, expected_type in zip(results, expected_types):
            assert isinstance(result, expected_type), f"Expected {expected_type}, got {type(result)}"
            assert result.confidence > 0
            assert len(result.analysis) > 0

        # =====================================================================
        # Phase 3: Verify Session State
        # =====================================================================

        # All agents should have the architect's decision
        for name, agent in team.items():
            if name != "architect":
                decisions = agent.get_decisions()
                assert len(decisions) >= 1, f"{name} should have architect's decision"

        # LLM client should have been called 7 times (1 + 6)
        assert llm_client.call_count == 7

    @pytest.mark.asyncio
    async def test_context_propagation(self, team, llm_client):
        """Test that context is properly passed between agents."""
        feature_name = "Payment Processing"

        # Set up architect with initial context
        team["architect"].set_feature_name(feature_name)
        team["architect"].set_context({
            "existing_tech": ["FastAPI", "PostgreSQL", "Redis"],
            "compliance": ["PCI-DSS"],
        })

        # Architect makes initial design
        arch_response = await team["architect"].execute_task_with_llm(
            "Design payment processing architecture"
        )

        # Backend receives architect's context and decisions
        team["backend"].set_feature_name(feature_name)
        team["backend"].set_context({
            "architecture": arch_response.approach,
            "tech_stack": ["FastAPI", "PostgreSQL"],
        })
        team["backend"].add_decision(DecisionJournal(
            user_id="test",
            title="Payment Architecture Approved",
            description=arch_response.analysis[:100],
            category="architecture",
            decision_type="technical",
        ))

        # Backend generates API design
        backend_response = await team["backend"].execute_task_with_llm(
            "Design payment API endpoints based on approved architecture"
        )

        # Verify context was in the prompt
        last_prompt = llm_client.last_prompt
        assert "Payment Architecture Approved" in last_prompt or "architecture" in last_prompt.lower()

        assert isinstance(backend_response, BackendResponse)

    @pytest.mark.asyncio
    async def test_session_with_custom_responses(self, llm_client):
        """Test session with custom mock responses for specific scenarios."""
        # Set up custom response for security findings
        security_response_data = {
            "analysis": "Critical security review completed",
            "approach": "Defense in depth strategy",
            "decisions": [
                {
                    "text": "Implement MFA",
                    "rationale": "Reduce account takeover risk",
                    "category": "security",
                }
            ],
            "concerns": ["Password hashing algorithm needs upgrade"],
            "confidence": 0.95,
            "vulnerabilities": [
                {"name": "Weak password policy", "severity": "medium"}
            ],
            "risk_level": "medium",
            "mitigations": ["Implement bcrypt", "Add rate limiting"],
            "compliance_notes": ["OWASP compliance verified"],
        }

        llm_client.set_custom_response("security", security_response_data)

        agent = SecuritySpecialistAgent(llm_client=llm_client)
        agent.set_feature_name("Auth Review")

        response = await agent.execute_task_with_llm(
            "Security review of authentication"
        )

        # Should get our custom response
        assert response.confidence == 0.95
        assert response.risk_level == "medium"
        assert "Implement MFA" in response.decisions[0].text


class TestSessionErrorHandling:
    """Test error handling in session scenarios."""

    def test_agent_without_llm_client(self):
        """Agent without LLM client should raise clear error."""
        agent = ArchitectAgent()  # No LLM client

        with pytest.raises(ValueError) as exc_info:
            asyncio.run(agent.execute_task_with_llm("Design system"))

        assert "No LLM client configured" in str(exc_info.value)

    def test_mock_fallback_works(self):
        """Mock execution should work when LLM not configured."""
        agent = BackendAgent()  # No LLM client

        # Synchronous mock execution should still work
        result = agent.execute_task("Design API")

        assert result["status"] == "started"
        assert result["agent"] == "Backend Developer"


class TestClientCreation:
    """Test client factory patterns."""

    def test_create_mock_for_testing(self):
        """Factory should create mock for testing."""
        client = create_client(use_mock=True)

        assert isinstance(client, MockLLMClient)

    def test_factory_pattern_for_team(self):
        """Demonstrate factory pattern for creating team."""
        # In production, this would use use_mock=False
        client = create_client(use_mock=True)

        team = [
            ArchitectAgent(llm_client=client),
            BackendAgent(llm_client=client),
            FrontendAgent(llm_client=client),
            SecuritySpecialistAgent(llm_client=client),
            DBAAgent(llm_client=client),
            UIUXDesignerAgent(llm_client=client),
            ITAdminAgent(llm_client=client),
        ]

        # All agents share the same client
        for agent in team:
            assert agent.llm_client is client


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
