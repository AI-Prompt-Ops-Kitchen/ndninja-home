"""Tests for task chain orchestration Celery tasks.

This module tests the orchestration tasks which coordinate multi-agent
execution using Celery's chain and group primitives.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone, timedelta


class TestStartSessionExecutionCreatesTasks:
    """Test that start_session_execution creates AgentTask records."""

    @patch('sage_mode.tasks.orchestration.chain')
    @patch('sage_mode.tasks.orchestration.group')
    @patch('sage_mode.tasks.orchestration.SessionLocal')
    def test_start_session_execution_creates_tasks(self, mock_session_local, mock_group, mock_chain):
        """AgentTask records are created for each task spec."""
        from sage_mode.tasks.orchestration import start_session_execution
        from sage_mode.models.session_model import ExecutionSession
        from sage_mode.models.task_model import AgentTask

        # Create mock session
        mock_session = MagicMock(spec=ExecutionSession)
        mock_session.id = 1

        # Setup mock database
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db
        mock_db.query.return_value.filter.return_value.first.return_value = mock_session

        # Track added tasks
        added_tasks = []

        def track_add(obj):
            if isinstance(obj, AgentTask):
                obj.id = len(added_tasks) + 1
                added_tasks.append(obj)

        mock_db.add.side_effect = track_add

        # Mock flush to assign IDs
        def mock_flush():
            pass
        mock_db.flush.side_effect = mock_flush

        # Setup chain mock
        mock_workflow = MagicMock()
        mock_workflow.apply_async.return_value = MagicMock(id="chain-123")
        mock_chain.return_value = mock_workflow

        task_specs = [
            {"agent_role": "frontend_developer", "task_description": "Build UI"},
            {"agent_role": "backend_developer", "task_description": "Build API"},
        ]

        result = start_session_execution.run(1, task_specs)

        # Verify tasks were created
        assert len(added_tasks) == 2
        assert added_tasks[0].agent_role == "frontend_developer"
        assert added_tasks[0].task_description == "Build UI"
        assert added_tasks[0].status == "pending"
        assert added_tasks[1].agent_role == "backend_developer"
        assert added_tasks[1].task_description == "Build API"


class TestStartSessionExecutionReturnsTaskIds:
    """Test that start_session_execution returns created task IDs."""

    @patch('sage_mode.tasks.orchestration.chain')
    @patch('sage_mode.tasks.orchestration.group')
    @patch('sage_mode.tasks.orchestration.SessionLocal')
    def test_start_session_execution_returns_task_ids(self, mock_session_local, mock_group, mock_chain):
        """Returns dict with session_id, task_ids, and chain_id."""
        from sage_mode.tasks.orchestration import start_session_execution
        from sage_mode.models.session_model import ExecutionSession
        from sage_mode.models.task_model import AgentTask

        # Create mock session
        mock_session = MagicMock(spec=ExecutionSession)
        mock_session.id = 42

        # Setup mock database with task ID counter
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db
        mock_db.query.return_value.filter.return_value.first.return_value = mock_session

        # Track task ID assignment
        task_id_counter = [0]

        def mock_add(obj):
            if hasattr(obj, 'id') and obj.id is None:
                task_id_counter[0] += 1

        def mock_flush():
            # Simulate ID assignment by getting the last added object
            pass

        mock_db.add.side_effect = mock_add

        # Use a more realistic approach - track added objects
        added_objects = []
        original_add = mock_db.add.side_effect

        def track_add(obj):
            if hasattr(obj, 'session_id'):  # AgentTask check
                added_objects.append(obj)
                obj.id = len(added_objects)

        mock_db.add.side_effect = track_add

        # Setup chain mock
        mock_workflow = MagicMock()
        mock_workflow.apply_async.return_value = MagicMock(id="chain-456")
        mock_chain.return_value = mock_workflow

        task_specs = [
            {"agent_role": "frontend_developer", "task_description": "Build UI"},
            {"agent_role": "backend_developer", "task_description": "Build API"},
            {"agent_role": "software_architect", "task_description": "Design system"},
        ]

        result = start_session_execution.run(42, task_specs)

        # Verify return structure
        assert result["session_id"] == 42
        assert len(result["task_ids"]) == 3
        assert result["task_ids"] == [1, 2, 3]
        assert result["chain_id"] == "chain-456"


class TestStartSessionExecutionInvalidSession:
    """Test that start_session_execution fails for non-existent session."""

    @patch('sage_mode.tasks.orchestration.SessionLocal')
    def test_start_session_execution_invalid_session(self, mock_session_local):
        """Fails with ValueError for non-existent session."""
        from sage_mode.tasks.orchestration import start_session_execution

        # Setup mock database to return None (session not found)
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db
        mock_db.query.return_value.filter.return_value.first.return_value = None

        task_specs = [
            {"agent_role": "frontend_developer", "task_description": "Build UI"},
        ]

        with pytest.raises(ValueError) as exc_info:
            start_session_execution.run(999, task_specs)

        assert "Session 999 not found" in str(exc_info.value)


class TestCompleteSessionUpdatesStatus:
    """Test that complete_session updates session status."""

    @patch('sage_mode.tasks.orchestration.SessionLocal')
    def test_complete_session_updates_status(self, mock_session_local):
        """Session status is marked as completed."""
        from sage_mode.tasks.orchestration import complete_session
        from sage_mode.models.session_model import ExecutionSession

        # Create mock session
        mock_session = MagicMock(spec=ExecutionSession)
        mock_session.id = 1
        mock_session.status = "active"
        mock_session.started_at = datetime.now(timezone.utc).replace(tzinfo=None)

        # Setup mock database
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db
        mock_db.query.return_value.filter.return_value.first.return_value = mock_session

        task_results = [
            {"task_id": 1, "status": "completed", "result": {}},
            {"task_id": 2, "status": "completed", "result": {}},
        ]

        result = complete_session.run(task_results, 1)

        # Verify status was updated
        assert mock_session.status == "completed"
        assert mock_session.ended_at is not None
        assert mock_db.commit.called

        # Verify return structure
        assert result["session_id"] == 1
        assert result["status"] == "completed"
        assert result["task_count"] == 2


class TestCompleteSessionCalculatesDuration:
    """Test that complete_session calculates duration correctly."""

    @patch('sage_mode.tasks.orchestration.SessionLocal')
    def test_complete_session_calculates_duration(self, mock_session_local):
        """Duration is calculated from session start to completion."""
        from sage_mode.tasks.orchestration import complete_session
        from sage_mode.models.session_model import ExecutionSession

        # Create mock session with a known start time
        mock_session = MagicMock(spec=ExecutionSession)
        mock_session.id = 1
        mock_session.status = "active"
        # Start time was 60 seconds ago
        mock_session.started_at = (
            datetime.now(timezone.utc) - timedelta(seconds=60)
        ).replace(tzinfo=None)

        # Track duration_seconds assignment
        duration_set = []

        def set_duration(value):
            duration_set.append(value)

        type(mock_session).duration_seconds = property(
            lambda self: duration_set[-1] if duration_set else None,
            lambda self, v: set_duration(v)
        )

        # Setup mock database
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db
        mock_db.query.return_value.filter.return_value.first.return_value = mock_session

        task_results = [{"task_id": 1, "status": "completed", "result": {}}]

        result = complete_session.run(task_results, 1)

        # Verify duration was calculated (should be approximately 60 seconds)
        assert len(duration_set) > 0
        assert duration_set[-1] >= 60  # At least 60 seconds
        assert duration_set[-1] < 70  # But not too long (test shouldn't take 10 seconds)


class TestExecuteSequentialTasks:
    """Test that execute_sequential_tasks works correctly."""

    @patch('sage_mode.tasks.orchestration.chain')
    @patch('sage_mode.tasks.orchestration.SessionLocal')
    def test_execute_sequential_tasks(self, mock_session_local, mock_chain):
        """Sequential execution creates tasks and returns correct structure."""
        from sage_mode.tasks.orchestration import execute_sequential_tasks
        from sage_mode.models.task_model import AgentTask

        # Setup mock database
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db

        # Track added tasks
        added_tasks = []

        def track_add(obj):
            if hasattr(obj, 'session_id'):  # AgentTask check
                added_tasks.append(obj)
                obj.id = len(added_tasks)

        mock_db.add.side_effect = track_add

        # Setup chain mock
        mock_workflow = MagicMock()
        mock_workflow.apply_async.return_value = MagicMock(id="seq-chain-789")
        mock_chain.return_value = mock_workflow

        task_specs = [
            {"agent_role": "software_architect", "task_description": "Design architecture"},
            {"agent_role": "backend_developer", "task_description": "Implement design"},
        ]

        result = execute_sequential_tasks.run(1, task_specs)

        # Verify tasks were created
        assert len(added_tasks) == 2
        assert added_tasks[0].agent_role == "software_architect"
        assert added_tasks[1].agent_role == "backend_developer"

        # Verify return structure
        assert result["session_id"] == 1
        assert len(result["task_ids"]) == 2
        assert result["chain_id"] == "seq-chain-789"

        # Verify chain was called (not group - sequential execution)
        assert mock_chain.called


class TestExecuteSequentialTasksWithInputData:
    """Test that execute_sequential_tasks handles input_data correctly."""

    @patch('sage_mode.tasks.orchestration.chain')
    @patch('sage_mode.tasks.orchestration.SessionLocal')
    def test_execute_sequential_tasks_with_input_data(self, mock_session_local, mock_chain):
        """Input data is passed to AgentTask records."""
        from sage_mode.tasks.orchestration import execute_sequential_tasks

        # Setup mock database
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db

        # Track added tasks
        added_tasks = []

        def track_add(obj):
            if hasattr(obj, 'session_id'):
                added_tasks.append(obj)
                obj.id = len(added_tasks)

        mock_db.add.side_effect = track_add

        # Setup chain mock
        mock_workflow = MagicMock()
        mock_workflow.apply_async.return_value = MagicMock(id="chain-input")
        mock_chain.return_value = mock_workflow

        task_specs = [
            {
                "agent_role": "frontend_developer",
                "task_description": "Build component",
                "input_data": {"framework": "React", "styling": "Tailwind"}
            },
        ]

        result = execute_sequential_tasks.run(1, task_specs)

        # Verify input_data was stored
        assert len(added_tasks) == 1
        assert added_tasks[0].input_data == {"framework": "React", "styling": "Tailwind"}


class TestStartSessionExecutionStoresChainId:
    """Test that start_session_execution stores the chain ID in the session."""

    @patch('sage_mode.tasks.orchestration.chain')
    @patch('sage_mode.tasks.orchestration.group')
    @patch('sage_mode.tasks.orchestration.SessionLocal')
    def test_start_session_execution_stores_chain_id(self, mock_session_local, mock_group, mock_chain):
        """Chain ID is stored in the session record."""
        from sage_mode.tasks.orchestration import start_session_execution
        from sage_mode.models.session_model import ExecutionSession

        # Create mock session
        mock_session = MagicMock(spec=ExecutionSession)
        mock_session.id = 1
        mock_session.celery_chain_id = None

        # Setup mock database
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db
        mock_db.query.return_value.filter.return_value.first.return_value = mock_session

        # Track added tasks with IDs
        def track_add(obj):
            if hasattr(obj, 'session_id'):
                obj.id = 1

        mock_db.add.side_effect = track_add

        # Setup chain mock
        mock_workflow = MagicMock()
        mock_workflow.apply_async.return_value = MagicMock(id="stored-chain-id")
        mock_chain.return_value = mock_workflow

        task_specs = [
            {"agent_role": "frontend_developer", "task_description": "Build UI"},
        ]

        result = start_session_execution.run(1, task_specs)

        # Verify chain ID was stored in session
        assert mock_session.celery_chain_id == "stored-chain-id"
        assert mock_db.commit.called


class TestCompleteSessionHandlesNoSession:
    """Test that complete_session handles missing session gracefully."""

    @patch('sage_mode.tasks.orchestration.SessionLocal')
    def test_complete_session_handles_no_session(self, mock_session_local):
        """Returns result even if session is not found."""
        from sage_mode.tasks.orchestration import complete_session

        # Setup mock database to return None
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db
        mock_db.query.return_value.filter.return_value.first.return_value = None

        task_results = [{"task_id": 1, "status": "completed", "result": {}}]

        # Should not raise, just return result
        result = complete_session.run(task_results, 999)

        # Verify return structure is still valid
        assert result["session_id"] == 999
        assert result["status"] == "completed"
        assert result["task_count"] == 1
