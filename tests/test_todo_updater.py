"""
Comprehensive tests for TodoUpdater - action item status tracking.

Tests cover:
- High-confidence (≥80%) auto-updates
- Medium-confidence (60-80%) pending_review marking
- Low-confidence (<60%) skipping
- Todo matching logic
- Edge cases and boundary conditions
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from tools_db.tools.keyword_detector import DetectionResult
from tools_db.tools.todo_updater import TodoUpdater, UpdateResult


class TestTodoUpdaterInit:
    """Test TodoUpdater initialization"""

    def test_todo_updater_initialization(self):
        """Test that TodoUpdater initializes correctly"""
        updater = TodoUpdater()
        assert updater is not None
        assert hasattr(updater, 'update_todo_from_detection')


class TestHighConfidenceAutoUpdate:
    """Test high-confidence (≥80%) auto-updates to 'completed'"""

    @patch('tools_db.tools.todo_updater.TodoUpdater._query_memory_todos')
    @patch('tools_db.tools.todo_updater.TodoUpdater._update_memory_todo')
    def test_high_confidence_updates_to_completed(self, mock_update, mock_query):
        """Test that ≥80% confidence auto-updates todo to completed"""
        # Arrange
        detection = DetectionResult(
            keyword_found="git commit",
            confidence=95,
            category="commit-related",
            context_snippet="git commit -m 'feat: implement feature X'"
        )

        mock_query.return_value = [
            {
                'id': 'task-123',
                'title': 'Implement feature X',
                'status': 'in_progress',
                'created_at': '2026-01-20T10:00:00Z'
            }
        ]

        mock_update.return_value = True

        updater = TodoUpdater()

        # Act
        result = updater.update_todo_from_detection(detection)

        # Assert
        assert result is not None
        assert result.updated is True
        assert result.todo_id == 'task-123'
        assert result.old_status == 'in_progress'
        assert result.new_status == 'completed'
        assert result.confidence == 95
        assert result.detected_keyword == 'git commit'
        mock_update.assert_called_once()

    @patch('tools_db.tools.todo_updater.TodoUpdater._query_memory_todos')
    @patch('tools_db.tools.todo_updater.TodoUpdater._update_memory_todo')
    def test_boundary_80_percent_confidence_updates(self, mock_update, mock_query):
        """Test that exactly 80% confidence auto-updates (boundary test)"""
        detection = DetectionResult(
            keyword_found="deployed",
            confidence=80,
            category="deployment",
            context_snippet="deployed successfully"
        )

        mock_query.return_value = [
            {'id': 'task-456', 'title': 'Deploy to production', 'status': 'in_progress', 'created_at': '2026-01-20T10:00:00Z'}
        ]
        mock_update.return_value = True

        updater = TodoUpdater()
        result = updater.update_todo_from_detection(detection)

        assert result.updated is True
        assert result.new_status == 'completed'

    @patch('tools_db.tools.todo_updater.TodoUpdater._query_memory_todos')
    @patch('tools_db.tools.todo_updater.TodoUpdater._update_memory_todo')
    def test_81_percent_confidence_updates(self, mock_update, mock_query):
        """Test that 81% confidence auto-updates"""
        detection = DetectionResult(
            keyword_found="all tests passed",
            confidence=81,
            category="test-success",
            context_snippet="all tests passed"
        )

        mock_query.return_value = [
            {'id': 'task-789', 'title': 'Run tests', 'status': 'in_progress', 'created_at': '2026-01-20T10:00:00Z'}
        ]
        mock_update.return_value = True

        updater = TodoUpdater()
        result = updater.update_todo_from_detection(detection)

        assert result.updated is True
        assert result.new_status == 'completed'


class TestMediumConfidencePendingReview:
    """Test medium-confidence (60-80%) marking as pending_review"""

    @patch('tools_db.tools.todo_updater.TodoUpdater._query_memory_todos')
    @patch('tools_db.tools.todo_updater.TodoUpdater._update_memory_todo')
    def test_medium_confidence_marks_pending_review(self, mock_update, mock_query):
        """Test that 60-80% confidence marks todo as pending_review"""
        detection = DetectionResult(
            keyword_found="fixed",
            confidence=75,
            category="bug-fixed",
            context_snippet="bug fixed"
        )

        mock_query.return_value = [
            {'id': 'task-001', 'title': 'Fix authentication bug', 'status': 'in_progress', 'created_at': '2026-01-20T10:00:00Z'}
        ]
        mock_update.return_value = True

        updater = TodoUpdater()
        result = updater.update_todo_from_detection(detection)

        assert result.updated is True
        assert result.new_status == 'pending_review'
        assert result.confidence == 75

    @patch('tools_db.tools.todo_updater.TodoUpdater._query_memory_todos')
    @patch('tools_db.tools.todo_updater.TodoUpdater._update_memory_todo')
    def test_boundary_60_percent_pending_review(self, mock_update, mock_query):
        """Test that exactly 60% confidence marks as pending_review (boundary)"""
        detection = DetectionResult(
            keyword_found="created",
            confidence=60,
            category="file-created",
            context_snippet="file created"
        )

        mock_query.return_value = [
            {'id': 'task-002', 'title': 'Create config file', 'status': 'in_progress', 'created_at': '2026-01-20T10:00:00Z'}
        ]
        mock_update.return_value = True

        updater = TodoUpdater()
        result = updater.update_todo_from_detection(detection)

        assert result.updated is True
        assert result.new_status == 'pending_review'

    @patch('tools_db.tools.todo_updater.TodoUpdater._query_memory_todos')
    @patch('tools_db.tools.todo_updater.TodoUpdater._update_memory_todo')
    def test_boundary_79_percent_pending_review(self, mock_update, mock_query):
        """Test that 79% confidence marks as pending_review (below auto-update threshold)"""
        detection = DetectionResult(
            keyword_found="resolved",
            confidence=79,
            category="bug-fixed",
            context_snippet="issue resolved"
        )

        mock_query.return_value = [
            {'id': 'task-003', 'title': 'Resolve issue', 'status': 'in_progress', 'created_at': '2026-01-20T10:00:00Z'}
        ]
        mock_update.return_value = True

        updater = TodoUpdater()
        result = updater.update_todo_from_detection(detection)

        assert result.updated is True
        assert result.new_status == 'pending_review'


class TestLowConfidenceSkipped:
    """Test that low-confidence (<60%) is skipped"""

    @patch('tools_db.tools.todo_updater.TodoUpdater._query_memory_todos')
    @patch('tools_db.tools.todo_updater.TodoUpdater._update_memory_todo')
    def test_low_confidence_skipped(self, mock_update, mock_query):
        """Test that <60% confidence is skipped (not updated)"""
        detection = DetectionResult(
            keyword_found="completed",
            confidence=55,
            category="build-success",
            context_snippet="task completed"
        )

        mock_query.return_value = [
            {'id': 'task-004', 'title': 'Build project', 'status': 'in_progress', 'created_at': '2026-01-20T10:00:00Z'}
        ]

        updater = TodoUpdater()
        result = updater.update_todo_from_detection(detection)

        assert result.updated is False
        assert result.reason == 'low_confidence'
        mock_update.assert_not_called()

    @patch('tools_db.tools.todo_updater.TodoUpdater._query_memory_todos')
    @patch('tools_db.tools.todo_updater.TodoUpdater._update_memory_todo')
    def test_boundary_59_percent_skipped(self, mock_update, mock_query):
        """Test that 59% confidence is skipped (boundary)"""
        detection = DetectionResult(
            keyword_found="done",
            confidence=59,
            category="test-success",
            context_snippet="done"
        )

        mock_query.return_value = [
            {'id': 'task-005', 'title': 'Run test', 'status': 'in_progress', 'created_at': '2026-01-20T10:00:00Z'}
        ]

        updater = TodoUpdater()
        result = updater.update_todo_from_detection(detection)

        assert result.updated is False
        mock_update.assert_not_called()


class TestNoMatchingTodos:
    """Test behavior when no matching todos found"""

    @patch('tools_db.tools.todo_updater.TodoUpdater._query_memory_todos')
    @patch('tools_db.tools.todo_updater.TodoUpdater._update_memory_todo')
    def test_no_matching_todos_noop(self, mock_update, mock_query):
        """Test that no matching todos results in no-op"""
        detection = DetectionResult(
            keyword_found="git commit",
            confidence=95,
            category="commit-related",
            context_snippet="git commit -m 'feat: something'"
        )

        # No todos in memory
        mock_query.return_value = []

        updater = TodoUpdater()
        result = updater.update_todo_from_detection(detection)

        assert result.updated is False
        assert result.reason == 'no_matching_todos'
        mock_update.assert_not_called()

    @patch('tools_db.tools.todo_updater.TodoUpdater._query_memory_todos')
    @patch('tools_db.tools.todo_updater.TodoUpdater._update_memory_todo')
    def test_empty_todo_list_noop(self, mock_update, mock_query):
        """Test that empty todo list is safe (no-op)"""
        detection = DetectionResult(
            keyword_found="deployed",
            confidence=90,
            category="deployment",
            context_snippet="deployed"
        )

        mock_query.return_value = []

        updater = TodoUpdater()
        result = updater.update_todo_from_detection(detection)

        assert result.updated is False
        assert result.reason == 'no_matching_todos'


class TestInProgressStateMatching:
    """Test that only 'in_progress' todos are matched"""

    @patch('tools_db.tools.todo_updater.TodoUpdater._query_memory_todos')
    @patch('tools_db.tools.todo_updater.TodoUpdater._update_memory_todo')
    def test_only_matches_in_progress_todos(self, mock_update, mock_query):
        """Test that completed todos are not matched"""
        detection = DetectionResult(
            keyword_found="fixed",
            confidence=85,
            category="bug-fixed",
            context_snippet="fixed"
        )

        # Mix of different status todos
        mock_query.return_value = [
            {'id': 'task-100', 'title': 'Fix bug A', 'status': 'completed', 'created_at': '2026-01-20T09:00:00Z'},
            {'id': 'task-101', 'title': 'Fix bug B', 'status': 'pending', 'created_at': '2026-01-20T10:00:00Z'},
            {'id': 'task-102', 'title': 'Fix bug C', 'status': 'in_progress', 'created_at': '2026-01-20T11:00:00Z'},
        ]
        mock_update.return_value = True

        updater = TodoUpdater()
        result = updater.update_todo_from_detection(detection)

        assert result.updated is True
        assert result.todo_id == 'task-102'
        assert result.old_status == 'in_progress'

    @patch('tools_db.tools.todo_updater.TodoUpdater._query_memory_todos')
    @patch('tools_db.tools.todo_updater.TodoUpdater._update_memory_todo')
    def test_ignores_completed_todos(self, mock_update, mock_query):
        """Test that completed todos are ignored"""
        detection = DetectionResult(
            keyword_found="created",
            confidence=85,
            category="file-created",
            context_snippet="created"
        )

        mock_query.return_value = [
            {'id': 'task-200', 'title': 'Create file', 'status': 'completed', 'created_at': '2026-01-20T10:00:00Z'}
        ]

        updater = TodoUpdater()
        result = updater.update_todo_from_detection(detection)

        assert result.updated is False
        assert result.reason == 'no_matching_todos'
        mock_update.assert_not_called()

    @patch('tools_db.tools.todo_updater.TodoUpdater._query_memory_todos')
    @patch('tools_db.tools.todo_updater.TodoUpdater._update_memory_todo')
    def test_ignores_pending_todos(self, mock_update, mock_query):
        """Test that pending todos are ignored (user must start them)"""
        detection = DetectionResult(
            keyword_found="resolved",
            confidence=85,
            category="bug-fixed",
            context_snippet="resolved"
        )

        mock_query.return_value = [
            {'id': 'task-300', 'title': 'Resolve issue', 'status': 'pending', 'created_at': '2026-01-20T10:00:00Z'}
        ]

        updater = TodoUpdater()
        result = updater.update_todo_from_detection(detection)

        assert result.updated is False
        assert result.reason == 'no_matching_todos'
        mock_update.assert_not_called()


class TestMultipleInProgressTodos:
    """Test handling of multiple in_progress todos"""

    @patch('tools_db.tools.todo_updater.TodoUpdater._query_memory_todos')
    @patch('tools_db.tools.todo_updater.TodoUpdater._update_memory_todo')
    def test_updates_most_recent_in_progress(self, mock_update, mock_query):
        """Test that most recent in_progress todo is updated"""
        detection = DetectionResult(
            keyword_found="git commit",
            confidence=90,
            category="commit-related",
            context_snippet="git commit"
        )

        # Multiple in_progress todos
        mock_query.return_value = [
            {'id': 'task-500', 'title': 'First task', 'status': 'in_progress', 'created_at': '2026-01-20T08:00:00Z'},
            {'id': 'task-501', 'title': 'Second task', 'status': 'in_progress', 'created_at': '2026-01-20T09:00:00Z'},
            {'id': 'task-502', 'title': 'Third task', 'status': 'in_progress', 'created_at': '2026-01-20T10:00:00Z'},
        ]
        mock_update.return_value = True

        updater = TodoUpdater()
        result = updater.update_todo_from_detection(detection)

        assert result.updated is True
        # Should update the most recent (task-502)
        assert result.todo_id == 'task-502'

    @patch('tools_db.tools.todo_updater.TodoUpdater._query_memory_todos')
    @patch('tools_db.tools.todo_updater.TodoUpdater._update_memory_todo')
    def test_only_one_in_progress_updated(self, mock_update, mock_query):
        """Test that exactly one todo is updated"""
        detection = DetectionResult(
            keyword_found="fixed",
            confidence=85,
            category="bug-fixed",
            context_snippet="fixed"
        )

        mock_query.return_value = [
            {'id': 'task-600', 'title': 'Task 1', 'status': 'in_progress', 'created_at': '2026-01-20T10:00:00Z'},
            {'id': 'task-601', 'title': 'Task 2', 'status': 'in_progress', 'created_at': '2026-01-20T11:00:00Z'},
        ]
        mock_update.return_value = True

        updater = TodoUpdater()
        result = updater.update_todo_from_detection(detection)

        assert result.updated is True
        # Should only update once
        mock_update.assert_called_once()


class TestCategoryKeywordMatching:
    """Test category-to-keyword matching logic"""

    @patch('tools_db.tools.todo_updater.TodoUpdater._query_memory_todos')
    @patch('tools_db.tools.todo_updater.TodoUpdater._update_memory_todo')
    def test_commit_related_keyword_matching(self, mock_update, mock_query):
        """Test commit-related keywords match 'Implement', 'Build', 'Deploy'"""
        detection = DetectionResult(
            keyword_found="git commit",
            confidence=90,
            category="commit-related",
            context_snippet="git commit"
        )

        mock_query.return_value = [
            {'id': 'task-700', 'title': 'Implement feature X', 'status': 'in_progress', 'created_at': '2026-01-20T10:00:00Z'}
        ]
        mock_update.return_value = True

        updater = TodoUpdater()
        result = updater.update_todo_from_detection(detection)

        assert result.updated is True

    @patch('tools_db.tools.todo_updater.TodoUpdater._query_memory_todos')
    @patch('tools_db.tools.todo_updater.TodoUpdater._update_memory_todo')
    def test_bug_fixed_keyword_matching(self, mock_update, mock_query):
        """Test bug-fixed keywords match 'Fix', 'Resolve'"""
        detection = DetectionResult(
            keyword_found="resolved",
            confidence=85,
            category="bug-fixed",
            context_snippet="resolved"
        )

        mock_query.return_value = [
            {'id': 'task-701', 'title': 'Fix authentication issue', 'status': 'in_progress', 'created_at': '2026-01-20T10:00:00Z'}
        ]
        mock_update.return_value = True

        updater = TodoUpdater()
        result = updater.update_todo_from_detection(detection)

        assert result.updated is True

    @patch('tools_db.tools.todo_updater.TodoUpdater._query_memory_todos')
    @patch('tools_db.tools.todo_updater.TodoUpdater._update_memory_todo')
    def test_file_created_keyword_matching(self, mock_update, mock_query):
        """Test file-created keywords match 'Create', 'Write'"""
        detection = DetectionResult(
            keyword_found="created",
            confidence=85,
            category="file-created",
            context_snippet="created"
        )

        mock_query.return_value = [
            {'id': 'task-702', 'title': 'Write test file', 'status': 'in_progress', 'created_at': '2026-01-20T10:00:00Z'}
        ]
        mock_update.return_value = True

        updater = TodoUpdater()
        result = updater.update_todo_from_detection(detection)

        assert result.updated is True


class TestIntegrationWithKeywordDetector:
    """Test integration with KeywordDetector output"""

    @patch('tools_db.tools.todo_updater.TodoUpdater._query_memory_todos')
    @patch('tools_db.tools.todo_updater.TodoUpdater._update_memory_todo')
    def test_with_real_detection_result(self, mock_update, mock_query):
        """Test with a real DetectionResult from KeywordDetector"""
        from tools_db.tools.keyword_detector import KeywordDetector

        detector = KeywordDetector()
        detection = detector.detect("git add -A && git commit -m 'feat: implement feature X'")

        assert detection is not None

        mock_query.return_value = [
            {'id': 'task-800', 'title': 'Implement feature X', 'status': 'in_progress', 'created_at': '2026-01-20T10:00:00Z'}
        ]
        mock_update.return_value = True

        updater = TodoUpdater()
        result = updater.update_todo_from_detection(detection)

        assert result.updated is True
        assert result.confidence >= 80


class TestUpdateResultStructure:
    """Test UpdateResult dataclass structure"""

    @patch('tools_db.tools.todo_updater.TodoUpdater._query_memory_todos')
    @patch('tools_db.tools.todo_updater.TodoUpdater._update_memory_todo')
    def test_update_result_has_required_fields(self, mock_update, mock_query):
        """Test that UpdateResult contains all required fields"""
        detection = DetectionResult(
            keyword_found="deployed",
            confidence=90,
            category="deployment",
            context_snippet="deployed"
        )

        mock_query.return_value = [
            {'id': 'task-900', 'title': 'Deploy app', 'status': 'in_progress', 'created_at': '2026-01-20T10:00:00Z'}
        ]
        mock_update.return_value = True

        updater = TodoUpdater()
        result = updater.update_todo_from_detection(detection)

        assert hasattr(result, 'updated')
        assert hasattr(result, 'todo_id')
        assert hasattr(result, 'old_status')
        assert hasattr(result, 'new_status')
        assert hasattr(result, 'confidence')
        assert hasattr(result, 'detected_keyword')
        assert hasattr(result, 'reason')
        assert result.updated is True

    @patch('tools_db.tools.todo_updater.TodoUpdater._query_memory_todos')
    def test_noop_result_has_reason(self, mock_query):
        """Test that no-op results include a reason"""
        detection = DetectionResult(
            keyword_found="test",
            confidence=50,
            category="test-success",
            context_snippet="test"
        )

        mock_query.return_value = []

        updater = TodoUpdater()
        result = updater.update_todo_from_detection(detection)

        assert result.updated is False
        assert result.reason is not None
        assert isinstance(result.reason, str)


class TestMemorySystemErrorHandling:
    """Test graceful handling of memory system errors"""

    @patch('tools_db.tools.todo_updater.TodoUpdater._query_memory_todos')
    def test_memory_query_error_handled(self, mock_query):
        """Test that errors in memory query are handled gracefully"""
        detection = DetectionResult(
            keyword_found="fixed",
            confidence=85,
            category="bug-fixed",
            context_snippet="fixed"
        )

        # Simulate memory system error
        mock_query.side_effect = Exception("Memory system unavailable")

        updater = TodoUpdater()
        result = updater.update_todo_from_detection(detection)

        assert result.updated is False
        assert 'error' in result.reason.lower() or result.reason == 'memory_system_error'

    @patch('tools_db.tools.todo_updater.TodoUpdater._query_memory_todos')
    @patch('tools_db.tools.todo_updater.TodoUpdater._update_memory_todo')
    def test_memory_update_error_handled(self, mock_update, mock_query):
        """Test that errors in memory update are handled gracefully"""
        detection = DetectionResult(
            keyword_found="resolved",
            confidence=85,
            category="bug-fixed",
            context_snippet="resolved"
        )

        mock_query.return_value = [
            {'id': 'task-1000', 'title': 'Resolve issue', 'status': 'in_progress', 'created_at': '2026-01-20T10:00:00Z'}
        ]
        mock_update.side_effect = Exception("Failed to update memory")

        updater = TodoUpdater()
        result = updater.update_todo_from_detection(detection)

        assert result.updated is False
        assert 'error' in result.reason.lower() or result.reason == 'update_failed'


class TestAuditTrailGeneration:
    """Test audit trail generation"""

    @patch('tools_db.tools.todo_updater.TodoUpdater._query_memory_todos')
    @patch('tools_db.tools.todo_updater.TodoUpdater._update_memory_todo')
    def test_update_result_contains_audit_info(self, mock_update, mock_query):
        """Test that result contains audit trail information"""
        detection = DetectionResult(
            keyword_found="git commit",
            confidence=95,
            category="commit-related",
            context_snippet="git commit -m 'feat: something'"
        )

        mock_query.return_value = [
            {'id': 'task-1100', 'title': 'Implement feature', 'status': 'in_progress', 'created_at': '2026-01-20T10:00:00Z'}
        ]
        mock_update.return_value = True

        updater = TodoUpdater()
        result = updater.update_todo_from_detection(detection)

        assert result.updated is True
        assert result.confidence == 95
        assert result.detected_keyword == 'git commit'
        assert result.old_status == 'in_progress'
        assert result.new_status == 'completed'
