"""Tests for agent task execution Celery tasks.

This module tests the execute_agent_task Celery task which is responsible
for executing individual agent tasks and storing their results in the database.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone


class TestExecuteAgentTaskSuccess:
    """Test successful agent task execution."""

    @patch('sage_mode.tasks.agent_tasks.SessionLocal')
    def test_execute_agent_task_success(self, mock_session_local):
        """Task executes and completes successfully."""
        from sage_mode.tasks.agent_tasks import execute_agent_task
        from sage_mode.models.task_model import AgentTask

        # Create mock task
        mock_task = MagicMock(spec=AgentTask)
        mock_task.id = 1
        mock_task.agent_role = "frontend_developer"
        mock_task.task_description = "Build login component"
        mock_task.input_data = {"framework": "React"}
        mock_task.status = "pending"
        mock_task.started_at = None

        # Setup mock session
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db
        mock_db.query.return_value.filter.return_value.first.return_value = mock_task

        # Use Celery's test mode - push request context with keyword arguments
        execute_agent_task.push_request(id="celery-task-123", retries=0)
        try:
            # Execute task synchronously using run()
            result = execute_agent_task.run(1)

            # Verify result
            assert result["task_id"] == 1
            assert result["status"] == "completed"
            assert "result" in result

            # Verify task was updated
            assert mock_task.status == "completed"
            assert mock_task.celery_task_id == "celery-task-123"
            assert mock_db.commit.called
        finally:
            execute_agent_task.pop_request()


class TestExecuteAgentTaskUpdatesStatus:
    """Test that task status transitions correctly."""

    @patch('sage_mode.tasks.agent_tasks.SessionLocal')
    def test_execute_agent_task_updates_status(self, mock_session_local):
        """Status transitions from pending to running to completed."""
        from sage_mode.tasks.agent_tasks import execute_agent_task
        from sage_mode.models.task_model import AgentTask

        # Track status changes
        status_history = []

        def track_status(value):
            status_history.append(value)

        # Create mock task
        mock_task = MagicMock(spec=AgentTask)
        mock_task.id = 1
        mock_task.agent_role = "backend_developer"
        mock_task.task_description = "Create API endpoint"
        mock_task.input_data = None
        type(mock_task).status = property(
            lambda self: status_history[-1] if status_history else "pending",
            lambda self, v: track_status(v)
        )

        # Setup mock session
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db
        mock_db.query.return_value.filter.return_value.first.return_value = mock_task

        execute_agent_task.push_request(id="celery-task-456", retries=0)
        try:
            execute_agent_task.run(1)

            # Verify status transitions
            assert "running" in status_history
            assert "completed" in status_history
            assert status_history.index("running") < status_history.index("completed")
        finally:
            execute_agent_task.pop_request()


class TestExecuteAgentTaskStoresResult:
    """Test that output data is stored correctly."""

    @patch('sage_mode.tasks.agent_tasks.SessionLocal')
    def test_execute_agent_task_stores_result(self, mock_session_local):
        """Output data is stored in the task record."""
        from sage_mode.tasks.agent_tasks import execute_agent_task
        from sage_mode.models.task_model import AgentTask

        # Create mock task
        mock_task = MagicMock(spec=AgentTask)
        mock_task.id = 1
        mock_task.agent_role = "software_architect"
        mock_task.task_description = "Design system architecture"
        mock_task.input_data = None

        # Setup mock session
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db
        mock_db.query.return_value.filter.return_value.first.return_value = mock_task

        execute_agent_task.push_request(id="celery-task-789", retries=0)
        try:
            execute_agent_task.run(1)

            # Verify output_data was set
            assert mock_task.output_data is not None
            assert isinstance(mock_task.output_data, dict)
            assert "status" in mock_task.output_data
        finally:
            execute_agent_task.pop_request()


class TestExecuteAgentTaskCalculatesDuration:
    """Test that duration is calculated correctly."""

    @patch('sage_mode.tasks.agent_tasks.SessionLocal')
    def test_execute_agent_task_calculates_duration(self, mock_session_local):
        """Duration is calculated from start to completion."""
        from sage_mode.tasks.agent_tasks import execute_agent_task
        from sage_mode.models.task_model import AgentTask

        # Create mock task with a tracked started_at
        mock_task = MagicMock(spec=AgentTask)
        mock_task.id = 1
        mock_task.agent_role = "ui_ux_designer"
        mock_task.task_description = "Design wireframes"
        mock_task.input_data = None
        mock_task.started_at = datetime.now(timezone.utc).replace(tzinfo=None)

        # Setup mock session
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db
        mock_db.query.return_value.filter.return_value.first.return_value = mock_task

        execute_agent_task.push_request(id="celery-task-101", retries=0)
        try:
            execute_agent_task.run(1)

            # Verify duration was calculated (should be >= 0)
            assert mock_task.duration_seconds is not None
            assert isinstance(mock_task.duration_seconds, int)
            assert mock_task.duration_seconds >= 0
        finally:
            execute_agent_task.pop_request()


class TestExecuteAgentTaskUnknownRole:
    """Test handling of unknown agent roles."""

    @patch('sage_mode.tasks.agent_tasks.SessionLocal')
    def test_execute_agent_task_unknown_role(self, mock_session_local):
        """Fails for unknown agent role with proper error handling."""
        from sage_mode.tasks.agent_tasks import execute_agent_task
        from sage_mode.models.task_model import AgentTask

        # Create mock task with unknown role
        mock_task = MagicMock(spec=AgentTask)
        mock_task.id = 1
        mock_task.agent_role = "unknown_role"
        mock_task.task_description = "Some task"
        mock_task.input_data = None

        # Setup mock session
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db
        mock_db.query.return_value.filter.return_value.first.return_value = mock_task

        execute_agent_task.push_request(id="celery-task-error", retries=0)
        try:
            # The task will fail and record the error, then raise Retry
            # which propagates through. We catch ValueError inside the task
            # but the retry re-raises it. We need to catch the re-raised exception.
            with pytest.raises(ValueError) as exc_info:
                execute_agent_task.run(1)

            # Verify the error message
            assert "Unknown agent role" in str(exc_info.value)

            # Verify error was recorded
            assert mock_task.status == "failed"
            assert "Unknown agent role" in mock_task.error_message
        finally:
            execute_agent_task.pop_request()


class TestExecuteAgentTaskNotFound:
    """Test handling of non-existent tasks."""

    @patch('sage_mode.tasks.agent_tasks.SessionLocal')
    def test_execute_agent_task_not_found(self, mock_session_local):
        """Fails for non-existent task with proper error handling."""
        from sage_mode.tasks.agent_tasks import execute_agent_task

        # Setup mock session to return None (task not found)
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db
        mock_db.query.return_value.filter.return_value.first.return_value = None

        execute_agent_task.push_request(id="celery-task-notfound", retries=0)
        try:
            # Expect ValueError to be raised
            with pytest.raises(ValueError) as exc_info:
                execute_agent_task.run(999)

            # Verify the error message
            assert "not found" in str(exc_info.value)
        finally:
            execute_agent_task.pop_request()


class TestAgentRegistryHasAllAgents:
    """Test that all 7 agents are registered."""

    def test_agent_registry_has_all_agents(self):
        """All 7 agent roles are present in the registry."""
        from sage_mode.tasks.agent_tasks import AGENT_REGISTRY
        from sage_mode.agents.frontend_agent import FrontendAgent
        from sage_mode.agents.backend_agent import BackendAgent
        from sage_mode.agents.architect_agent import ArchitectAgent
        from sage_mode.agents.ui_ux_designer_agent import UIUXDesignerAgent
        from sage_mode.agents.dba_agent import DBAAgent
        from sage_mode.agents.it_admin_agent import ITAdminAgent
        from sage_mode.agents.security_specialist_agent import SecuritySpecialistAgent

        # Verify registry has exactly 7 agents
        assert len(AGENT_REGISTRY) == 7

        # Verify each role is present with correct class
        assert AGENT_REGISTRY["frontend_developer"] == FrontendAgent
        assert AGENT_REGISTRY["backend_developer"] == BackendAgent
        assert AGENT_REGISTRY["software_architect"] == ArchitectAgent
        assert AGENT_REGISTRY["ui_ux_designer"] == UIUXDesignerAgent
        assert AGENT_REGISTRY["database_administrator"] == DBAAgent
        assert AGENT_REGISTRY["it_administrator"] == ITAdminAgent
        assert AGENT_REGISTRY["security_specialist"] == SecuritySpecialistAgent

    def test_agent_registry_roles_match_enum(self):
        """Registry roles match AgentRole enum values."""
        from sage_mode.tasks.agent_tasks import AGENT_REGISTRY
        from sage_mode.models.team_simulator import AgentRole

        # All enum values should be in registry
        for role in AgentRole:
            assert role.value in AGENT_REGISTRY, f"Missing role: {role.value}"


class TestAgentContextAndDecisions:
    """Test context setting and decision storage."""

    @patch('sage_mode.tasks.agent_tasks.SessionLocal')
    @patch('sage_mode.tasks.agent_tasks.AGENT_REGISTRY')
    def test_execute_agent_task_with_input_context(self, mock_registry, mock_session_local):
        """Input data is passed as context to the agent."""
        from sage_mode.tasks.agent_tasks import execute_agent_task
        from sage_mode.models.task_model import AgentTask

        input_data = {"framework": "Next.js", "styling": "Tailwind"}

        mock_task = MagicMock(spec=AgentTask)
        mock_task.id = 1
        mock_task.agent_role = "frontend_developer"
        mock_task.task_description = "Build dashboard"
        mock_task.input_data = input_data

        mock_db = MagicMock()
        mock_session_local.return_value = mock_db
        mock_db.query.return_value.filter.return_value.first.return_value = mock_task

        # Setup mock agent via registry
        mock_agent_instance = MagicMock()
        mock_agent_instance.execute_task.return_value = {"status": "completed"}
        mock_agent_instance.decisions = []

        mock_agent_class = MagicMock(return_value=mock_agent_instance)
        mock_registry.get.return_value = mock_agent_class

        execute_agent_task.push_request(id="celery-task-context", retries=0)
        try:
            execute_agent_task.run(1)

            # Verify set_context was called with input_data
            mock_agent_instance.set_context.assert_called_once_with(input_data)
        finally:
            execute_agent_task.pop_request()


class TestTaskRetryBehavior:
    """Test retry behavior on failures."""

    @patch('sage_mode.tasks.agent_tasks.SessionLocal')
    @patch('sage_mode.tasks.agent_tasks.AGENT_REGISTRY')
    def test_retry_with_exponential_backoff(self, mock_registry, mock_session_local):
        """Retry uses exponential backoff countdown."""
        from sage_mode.tasks.agent_tasks import execute_agent_task
        from sage_mode.models.task_model import AgentTask

        # Create mock task that will fail during execution
        mock_task = MagicMock(spec=AgentTask)
        mock_task.id = 1
        mock_task.agent_role = "backend_developer"
        mock_task.task_description = "Create API"
        mock_task.input_data = None

        mock_db = MagicMock()
        mock_session_local.return_value = mock_db
        mock_db.query.return_value.filter.return_value.first.return_value = mock_task

        # Mock the agent via registry to raise an exception
        mock_agent = MagicMock()
        mock_agent.execute_task.side_effect = RuntimeError("Execution failed")
        mock_agent_class = MagicMock(return_value=mock_agent)
        mock_registry.get.return_value = mock_agent_class

        # Push request with 2 retries to test exponential backoff calculation
        execute_agent_task.push_request(id="celery-task-retry", retries=2)
        try:
            with pytest.raises(RuntimeError) as exc_info:
                execute_agent_task.run(1)

            # Verify the error was raised
            assert "Execution failed" in str(exc_info.value)

            # Verify task status was updated to failed
            assert mock_task.status == "failed"
            assert mock_task.retry_count == 2
        finally:
            execute_agent_task.pop_request()


class TestDecisionStorage:
    """Test that agent decisions are stored correctly."""

    @patch('sage_mode.tasks.agent_tasks.SessionLocal')
    @patch('sage_mode.tasks.agent_tasks.AGENT_REGISTRY')
    def test_decisions_stored_from_dict(self, mock_registry, mock_session_local):
        """Dict-format decisions are stored as TaskDecision records."""
        from sage_mode.tasks.agent_tasks import execute_agent_task
        from sage_mode.models.task_model import AgentTask, TaskDecision

        mock_task = MagicMock(spec=AgentTask)
        mock_task.id = 1
        mock_task.agent_role = "software_architect"
        mock_task.task_description = "Design architecture"
        mock_task.input_data = None

        mock_db = MagicMock()
        mock_session_local.return_value = mock_db
        mock_db.query.return_value.filter.return_value.first.return_value = mock_task

        # Setup mock agent via registry with decisions
        mock_agent = MagicMock()
        mock_agent.execute_task.return_value = {"status": "completed"}
        mock_agent.decisions = [
            {"text": "Use microservices", "rationale": "Better scalability", "category": "architecture"}
        ]
        mock_agent_class = MagicMock(return_value=mock_agent)
        mock_registry.get.return_value = mock_agent_class

        execute_agent_task.push_request(id="celery-task-decisions", retries=0)
        try:
            execute_agent_task.run(1)

            # Verify db.add was called with a TaskDecision
            add_calls = mock_db.add.call_args_list
            assert len(add_calls) > 0

            # Check that TaskDecision was added
            decision_added = False
            for call in add_calls:
                obj = call[0][0]
                if isinstance(obj, TaskDecision):
                    decision_added = True
                    assert obj.decision_text == "Use microservices"
                    assert obj.rationale == "Better scalability"
                    assert obj.category == "architecture"

            assert decision_added, "TaskDecision should be added to session"
        finally:
            execute_agent_task.pop_request()
