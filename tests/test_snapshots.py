"""Tests for agent snapshot persistence Celery tasks.

This module tests the snapshot management tasks which enable:
- Saving agent state for debugging and auditing
- Retrieving all snapshots for a task
- Getting the latest snapshot for resume purposes
"""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime


class TestSaveAgentSnapshotSuccess:
    """Test successful snapshot saving."""

    @patch('sage_mode.tasks.snapshots.SessionLocal')
    def test_save_agent_snapshot_success(self, mock_session_local):
        """Snapshot saves correctly with all required fields."""
        from sage_mode.tasks.snapshots import save_agent_snapshot
        from sage_mode.models.task_model import AgentTask, AgentSnapshot

        # Create mock task (snapshot references this)
        mock_task = MagicMock(spec=AgentTask)
        mock_task.id = 1

        # Create mock snapshot that will be returned
        mock_snapshot = MagicMock(spec=AgentSnapshot)
        mock_snapshot.id = 100
        mock_snapshot.agent_task_id = 1
        mock_snapshot.agent_role = "backend_developer"
        mock_snapshot.context_state = {"current_step": "analyzing"}
        mock_snapshot.capabilities = ["api_design", "database"]
        mock_snapshot.decisions = [{"text": "Use REST API"}]
        mock_snapshot.execution_metadata = {"memory_usage": "256MB"}

        # Setup mock session
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db
        mock_db.query.return_value.filter.return_value.first.return_value = mock_task

        # Mock the add -> commit -> refresh cycle
        def capture_snapshot(obj):
            # Copy properties to the mock when add() is called
            mock_snapshot.agent_task_id = obj.agent_task_id
            mock_snapshot.agent_role = obj.agent_role

        mock_db.add.side_effect = capture_snapshot

        def do_refresh(obj):
            obj.id = 100

        mock_db.refresh.side_effect = do_refresh

        # Push request context for the Celery task
        save_agent_snapshot.push_request(id="celery-snapshot-1", retries=0)
        try:
            result = save_agent_snapshot.run(
                agent_task_id=1,
                agent_role="backend_developer",
                context_state={"current_step": "analyzing"},
                capabilities=["api_design", "database"],
                decisions=[{"text": "Use REST API"}],
                execution_metadata={"memory_usage": "256MB"}
            )

            # Verify success status
            assert result["status"] == "saved"
            assert result["agent_task_id"] == 1
            assert mock_db.commit.called
        finally:
            save_agent_snapshot.pop_request()


class TestSaveAgentSnapshotReturnsId:
    """Test that snapshot ID is returned."""

    @patch('sage_mode.tasks.snapshots.SessionLocal')
    def test_save_agent_snapshot_returns_id(self, mock_session_local):
        """Returns snapshot ID after successful save."""
        from sage_mode.tasks.snapshots import save_agent_snapshot
        from sage_mode.models.task_model import AgentTask

        mock_task = MagicMock(spec=AgentTask)
        mock_task.id = 1

        mock_db = MagicMock()
        mock_session_local.return_value = mock_db
        mock_db.query.return_value.filter.return_value.first.return_value = mock_task

        # Set the snapshot ID on refresh
        def do_refresh(obj):
            obj.id = 42

        mock_db.refresh.side_effect = do_refresh

        save_agent_snapshot.push_request(id="celery-snapshot-id", retries=0)
        try:
            result = save_agent_snapshot.run(
                agent_task_id=1,
                agent_role="frontend_developer",
                context_state={},
                capabilities=[],
                decisions=[]
            )

            assert "snapshot_id" in result
            assert result["snapshot_id"] == 42
        finally:
            save_agent_snapshot.pop_request()


class TestSaveAgentSnapshotInvalidTask:
    """Test handling of non-existent task."""

    @patch('sage_mode.tasks.snapshots.SessionLocal')
    def test_save_agent_snapshot_invalid_task(self, mock_session_local):
        """Fails for non-existent task with proper error."""
        from sage_mode.tasks.snapshots import save_agent_snapshot

        mock_db = MagicMock()
        mock_session_local.return_value = mock_db
        # Task not found
        mock_db.query.return_value.filter.return_value.first.return_value = None

        save_agent_snapshot.push_request(id="celery-snapshot-notfound", retries=0)
        try:
            with pytest.raises(ValueError) as exc_info:
                save_agent_snapshot.run(
                    agent_task_id=999,
                    agent_role="backend_developer",
                    context_state={},
                    capabilities=[],
                    decisions=[]
                )

            assert "not found" in str(exc_info.value)
            assert mock_db.rollback.called
        finally:
            save_agent_snapshot.pop_request()


class TestGetTaskSnapshots:
    """Test retrieving all snapshots for a task."""

    @patch('sage_mode.tasks.snapshots.SessionLocal')
    def test_get_task_snapshots(self, mock_session_local):
        """Returns all snapshots for task ordered by created_at."""
        from sage_mode.tasks.snapshots import get_task_snapshots
        from sage_mode.models.task_model import AgentSnapshot

        # Create mock snapshots
        snapshot1 = MagicMock(spec=AgentSnapshot)
        snapshot1.id = 1
        snapshot1.agent_role = "backend_developer"
        snapshot1.context_state = {"step": 1}
        snapshot1.capabilities = ["api"]
        snapshot1.decisions = []
        snapshot1.execution_metadata = {}
        snapshot1.created_at = datetime(2024, 1, 1, 10, 0, 0)

        snapshot2 = MagicMock(spec=AgentSnapshot)
        snapshot2.id = 2
        snapshot2.agent_role = "backend_developer"
        snapshot2.context_state = {"step": 2}
        snapshot2.capabilities = ["api", "db"]
        snapshot2.decisions = [{"text": "Use PostgreSQL"}]
        snapshot2.execution_metadata = {"progress": "50%"}
        snapshot2.created_at = datetime(2024, 1, 1, 10, 30, 0)

        mock_db = MagicMock()
        mock_session_local.return_value = mock_db
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [
            snapshot1, snapshot2
        ]

        result = get_task_snapshots.run(agent_task_id=1)

        assert len(result) == 2
        assert result[0]["id"] == 1
        assert result[0]["context_state"] == {"step": 1}
        assert result[1]["id"] == 2
        assert result[1]["decisions"] == [{"text": "Use PostgreSQL"}]
        assert result[1]["created_at"] == "2024-01-01T10:30:00"


class TestGetTaskSnapshotsEmpty:
    """Test retrieving snapshots when none exist."""

    @patch('sage_mode.tasks.snapshots.SessionLocal')
    def test_get_task_snapshots_empty(self, mock_session_local):
        """Returns empty list if no snapshots exist for task."""
        from sage_mode.tasks.snapshots import get_task_snapshots

        mock_db = MagicMock()
        mock_session_local.return_value = mock_db
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []

        result = get_task_snapshots.run(agent_task_id=999)

        assert result == []
        assert isinstance(result, list)


class TestGetLatestSnapshot:
    """Test retrieving the most recent snapshot."""

    @patch('sage_mode.tasks.snapshots.SessionLocal')
    def test_get_latest_snapshot(self, mock_session_local):
        """Returns most recent snapshot for resume purposes."""
        from sage_mode.tasks.snapshots import get_latest_snapshot
        from sage_mode.models.task_model import AgentSnapshot

        # Create mock of most recent snapshot
        latest_snapshot = MagicMock(spec=AgentSnapshot)
        latest_snapshot.id = 5
        latest_snapshot.agent_role = "software_architect"
        latest_snapshot.context_state = {"phase": "design_complete"}
        latest_snapshot.capabilities = ["architecture", "api_design"]
        latest_snapshot.decisions = [
            {"text": "Use microservices"},
            {"text": "Deploy to Kubernetes"}
        ]
        latest_snapshot.execution_metadata = {"iterations": 3}
        latest_snapshot.created_at = datetime(2024, 1, 15, 14, 30, 0)

        mock_db = MagicMock()
        mock_session_local.return_value = mock_db
        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = latest_snapshot

        result = get_latest_snapshot.run(agent_task_id=1)

        assert result is not None
        assert result["id"] == 5
        assert result["agent_role"] == "software_architect"
        assert result["context_state"] == {"phase": "design_complete"}
        assert len(result["decisions"]) == 2
        assert result["created_at"] == "2024-01-15T14:30:00"


class TestGetLatestSnapshotNone:
    """Test retrieving latest snapshot when none exist."""

    @patch('sage_mode.tasks.snapshots.SessionLocal')
    def test_get_latest_snapshot_none(self, mock_session_local):
        """Returns None if no snapshots exist for task."""
        from sage_mode.tasks.snapshots import get_latest_snapshot

        mock_db = MagicMock()
        mock_session_local.return_value = mock_db
        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None

        result = get_latest_snapshot.run(agent_task_id=999)

        assert result is None
