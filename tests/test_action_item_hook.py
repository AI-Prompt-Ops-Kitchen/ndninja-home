"""
Comprehensive tests for ActionItemHook - PostToolUse hook integration.

Tests cover:
- Full workflow: tool output → detection → todo update → event logged
- No keywords found
- Low confidence detection
- Medium confidence (pending_review)
- High confidence (completed)
- Todo update failures
- Database error handling
- Real bash output (git commit, pytest)
- Real write tool output
- Hook result structure
- Multiple rapid tool executions
- Unsupported tool names
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, call
from datetime import datetime, timezone
from dataclasses import dataclass

from tools_db.tools.action_item_hook import ActionItemHook, HookResult
from tools_db.tools.keyword_detector import KeywordDetector, DetectionResult
from tools_db.tools.todo_updater import TodoUpdater, UpdateResult
from tools_db.models import AutomationEvent


class TestActionItemHookInit:
    """Test ActionItemHook initialization"""

    def test_hook_initialization_with_hub(self):
        """Test that ActionItemHook initializes correctly with AutomationHub"""
        mock_hub = Mock()
        hook = ActionItemHook(automation_hub=mock_hub, test_mode=True)

        assert hook is not None
        assert hook.automation_hub == mock_hub
        assert hook.test_mode is True
        assert hasattr(hook, 'handle_tool_output')
        assert hasattr(hook, '_should_process_tool')
        assert hasattr(hook, '_create_detection_event')

    def test_hook_initialization_without_hub(self):
        """Test that ActionItemHook can initialize without hub (graceful fallback)"""
        hook = ActionItemHook(automation_hub=None, test_mode=True)

        assert hook is not None
        assert hook.automation_hub is None
        assert hook.test_mode is True


class TestShouldProcessTool:
    """Test tool filtering logic"""

    def test_should_process_bash_tool(self):
        """Test that bash tool output is marked for processing"""
        hook = ActionItemHook(automation_hub=Mock(), test_mode=True)
        assert hook._should_process_tool("bash") is True

    def test_should_process_write_tool(self):
        """Test that write tool output is marked for processing"""
        hook = ActionItemHook(automation_hub=Mock(), test_mode=True)
        assert hook._should_process_tool("write") is True

    def test_should_process_edit_tool(self):
        """Test that edit tool output is marked for processing"""
        hook = ActionItemHook(automation_hub=Mock(), test_mode=True)
        assert hook._should_process_tool("edit") is True

    def test_should_skip_unsupported_tool(self):
        """Test that unsupported tools are skipped"""
        hook = ActionItemHook(automation_hub=Mock(), test_mode=True)
        assert hook._should_process_tool("browser_click") is False
        assert hook._should_process_tool("read") is False
        assert hook._should_process_tool("unknown_tool") is False


class TestFullWorkflowSuccessfulCompletion:
    """Test successful complete workflow: detection → update → event logged"""

    @patch('tools_db.tools.action_item_hook.KeywordDetector')
    @patch('tools_db.tools.action_item_hook.TodoUpdater')
    def test_full_workflow_high_confidence_update(self, mock_updater_class, mock_detector_class):
        """Test successful workflow with high confidence detection and todo update"""
        # Arrange
        mock_hub = Mock()
        mock_hub.store_event.return_value = 123  # Event ID

        # Mock detector
        mock_detector_instance = Mock()
        mock_detector_class.return_value = mock_detector_instance
        detection_result = DetectionResult(
            keyword_found="git commit",
            confidence=95,
            category="commit-related",
            context_snippet="git commit -m 'feat: implement'"
        )
        mock_detector_instance.detect.return_value = detection_result

        # Mock updater
        mock_updater_instance = Mock()
        mock_updater_class.return_value = mock_updater_instance
        update_result = UpdateResult(
            updated=True,
            todo_id="task-123",
            old_status="in_progress",
            new_status="completed",
            confidence=95,
            detected_keyword="git commit",
            reason=None
        )
        mock_updater_instance.update_todo_from_detection.return_value = update_result

        hook = ActionItemHook(automation_hub=mock_hub, test_mode=True)

        # Act
        result = hook.handle_tool_output("bash", "git add -A && git commit -m 'feat: implement'")

        # Assert
        assert result is not None
        assert isinstance(result, HookResult)
        assert result.action_taken is True
        assert result.tool_name == "bash"
        assert result.keyword_found == "git commit"
        assert result.confidence == 95
        assert result.todo_updated is True
        assert result.todo_id == "task-123"
        assert result.new_status == "completed"
        assert result.reason == "updated_successfully"
        assert result.event_id == 123

        # Verify detector was called
        mock_detector_instance.detect.assert_called_once()

        # Verify updater was called
        mock_updater_instance.update_todo_from_detection.assert_called_once_with(detection_result)

        # Verify event was stored
        mock_hub.store_event.assert_called_once()

    @patch('tools_db.tools.action_item_hook.KeywordDetector')
    @patch('tools_db.tools.action_item_hook.TodoUpdater')
    def test_full_workflow_medium_confidence_pending_review(self, mock_updater_class, mock_detector_class):
        """Test workflow with medium confidence → pending_review status"""
        # Arrange
        mock_hub = Mock()
        mock_hub.store_event.return_value = 124

        mock_detector_instance = Mock()
        mock_detector_class.return_value = mock_detector_instance
        detection_result = DetectionResult(
            keyword_found="fixed",
            confidence=72,
            category="bug-fixed",
            context_snippet="bug fixed"
        )
        mock_detector_instance.detect.return_value = detection_result

        mock_updater_instance = Mock()
        mock_updater_class.return_value = mock_updater_instance
        update_result = UpdateResult(
            updated=True,
            todo_id="task-456",
            old_status="in_progress",
            new_status="pending_review",
            confidence=72,
            detected_keyword="fixed",
            reason=None
        )
        mock_updater_instance.update_todo_from_detection.return_value = update_result

        hook = ActionItemHook(automation_hub=mock_hub, test_mode=True)

        # Act
        result = hook.handle_tool_output("edit", "Bug fixed in authentication module")

        # Assert
        assert result.action_taken is True
        assert result.new_status == "pending_review"
        assert result.keyword_found == "fixed"
        assert result.confidence == 72


class TestNoKeywordsFound:
    """Test when no keywords are detected in tool output"""

    @patch('tools_db.tools.action_item_hook.KeywordDetector')
    @patch('tools_db.tools.action_item_hook.TodoUpdater')
    def test_no_keywords_found_returns_no_action(self, mock_updater_class, mock_detector_class):
        """Test that no keywords found → no action taken"""
        # Arrange
        mock_hub = Mock()
        mock_hub.store_event.return_value = None

        mock_detector_instance = Mock()
        mock_detector_class.return_value = mock_detector_instance
        mock_detector_instance.detect.return_value = None  # No detection

        hook = ActionItemHook(automation_hub=mock_hub, test_mode=True)

        # Act
        result = hook.handle_tool_output("bash", "Some random output without keywords")

        # Assert
        assert result is not None
        assert result.action_taken is False
        assert result.tool_name == "bash"
        assert result.keyword_found is None
        assert result.todo_updated is False
        assert result.reason == "no_keywords_found"

        # Updater should not be called
        mock_updater_class.assert_called()  # Detector was used
        mock_updater_class.return_value.update_todo_from_detection.assert_not_called()


class TestLowConfidenceSkipped:
    """Test when keyword detected but confidence too low"""

    @patch('tools_db.tools.action_item_hook.KeywordDetector')
    @patch('tools_db.tools.action_item_hook.TodoUpdater')
    def test_low_confidence_no_update(self, mock_updater_class, mock_detector_class):
        """Test that low confidence keywords don't trigger updates"""
        # Arrange
        mock_hub = Mock()

        mock_detector_instance = Mock()
        mock_detector_class.return_value = mock_detector_instance
        detection_result = DetectionResult(
            keyword_found="completed",
            confidence=45,  # Below 60% threshold
            category="build-success",
            context_snippet="task completed"
        )
        mock_detector_instance.detect.return_value = detection_result

        mock_updater_instance = Mock()
        mock_updater_class.return_value = mock_updater_instance

        hook = ActionItemHook(automation_hub=mock_hub, test_mode=True)

        # Act
        result = hook.handle_tool_output("bash", "Task completed")

        # Assert
        assert result.action_taken is False
        assert result.keyword_found == "completed"
        assert result.confidence == 45
        assert result.reason == "low_confidence"
        assert result.todo_updated is False


class TestTodoUpdateFailure:
    """Test when todo update fails in memory system"""

    @patch('tools_db.tools.action_item_hook.KeywordDetector')
    @patch('tools_db.tools.action_item_hook.TodoUpdater')
    def test_todo_update_fails_no_matching_todos(self, mock_updater_class, mock_detector_class):
        """Test when update fails because no matching in_progress todos"""
        # Arrange
        mock_hub = Mock()
        mock_hub.store_event.return_value = 125

        mock_detector_instance = Mock()
        mock_detector_class.return_value = mock_detector_instance
        detection_result = DetectionResult(
            keyword_found="deployed",
            confidence=88,
            category="deployment",
            context_snippet="deployed successfully"
        )
        mock_detector_instance.detect.return_value = detection_result

        mock_updater_instance = Mock()
        mock_updater_class.return_value = mock_updater_instance
        update_result = UpdateResult(
            updated=False,
            confidence=88,
            detected_keyword="deployed",
            reason="no_matching_todos"  # No in_progress todos to update
        )
        mock_updater_instance.update_todo_from_detection.return_value = update_result

        hook = ActionItemHook(automation_hub=mock_hub, test_mode=True)

        # Act
        result = hook.handle_tool_output("bash", "Application deployed successfully")

        # Assert
        assert result.action_taken is False
        assert result.todo_updated is False
        assert result.reason == "no_matching_todos"
        assert result.keyword_found == "deployed"
        assert result.confidence == 88


class TestDatabaseErrorHandling:
    """Test graceful handling when database/hub is unavailable"""

    def test_handle_tool_output_with_none_hub(self):
        """Test that hook gracefully handles missing hub (test mode)"""
        hook = ActionItemHook(automation_hub=None, test_mode=True)

        # Should not crash, returns result
        result = hook.handle_tool_output("bash", "git commit -m 'test'")

        assert result is not None
        assert isinstance(result, HookResult)

    @patch('tools_db.tools.action_item_hook.KeywordDetector')
    @patch('tools_db.tools.action_item_hook.TodoUpdater')
    def test_hub_store_event_failure_doesnt_crash(self, mock_updater_class, mock_detector_class):
        """Test that hub.store_event failure doesn't crash the hook"""
        # Arrange
        mock_hub = Mock()
        mock_hub.store_event.side_effect = Exception("Database connection failed")

        mock_detector_instance = Mock()
        mock_detector_class.return_value = mock_detector_instance
        detection_result = DetectionResult(
            keyword_found="git commit",
            confidence=95,
            category="commit-related",
            context_snippet="git commit"
        )
        mock_detector_instance.detect.return_value = detection_result

        mock_updater_instance = Mock()
        mock_updater_class.return_value = mock_updater_instance
        update_result = UpdateResult(
            updated=True,
            todo_id="task-123",
            old_status="in_progress",
            new_status="completed",
            confidence=95,
            detected_keyword="git commit",
            reason=None
        )
        mock_updater_instance.update_todo_from_detection.return_value = update_result

        hook = ActionItemHook(automation_hub=mock_hub, test_mode=True)

        # Act - should not crash
        result = hook.handle_tool_output("bash", "git commit -m 'test'")

        # Assert - still returns result
        assert result is not None
        assert result.action_taken is True  # Detection and update still succeeded
        assert result.event_id is None  # Event storage failed


class TestRealBashOutput:
    """Test with realistic bash command outputs"""

    @patch('tools_db.tools.action_item_hook.KeywordDetector')
    @patch('tools_db.tools.action_item_hook.TodoUpdater')
    def test_real_git_commit_output(self, mock_updater_class, mock_detector_class):
        """Test with realistic git commit output"""
        # Arrange
        mock_hub = Mock()
        mock_hub.store_event.return_value = 126

        mock_detector_instance = Mock()
        mock_detector_class.return_value = mock_detector_instance
        detection_result = DetectionResult(
            keyword_found="git commit",
            confidence=98,
            category="commit-related",
            context_snippet="git commit -m"
        )
        mock_detector_instance.detect.return_value = detection_result

        mock_updater_instance = Mock()
        mock_updater_class.return_value = mock_updater_instance
        update_result = UpdateResult(
            updated=True,
            todo_id="task-789",
            old_status="in_progress",
            new_status="completed",
            confidence=98,
            detected_keyword="git commit",
            reason=None
        )
        mock_updater_instance.update_todo_from_detection.return_value = update_result

        hook = ActionItemHook(automation_hub=mock_hub, test_mode=True)

        real_git_output = """
[master a1b2c3d] feat: add PostToolUse hook for action item completion tracking
 2 files changed, 150 insertions(+)
 create mode 100644 tools_db/tools/action_item_hook.py
 create mode 100644 tests/test_action_item_hook.py
"""

        # Act
        result = hook.handle_tool_output("bash", real_git_output)

        # Assert
        assert result.action_taken is True
        assert result.keyword_found == "git commit"
        assert result.confidence == 98

    @patch('tools_db.tools.action_item_hook.KeywordDetector')
    @patch('tools_db.tools.action_item_hook.TodoUpdater')
    def test_real_pytest_output_passing(self, mock_updater_class, mock_detector_class):
        """Test with realistic pytest passing output"""
        # Arrange
        mock_hub = Mock()
        mock_hub.store_event.return_value = 127

        mock_detector_instance = Mock()
        mock_detector_class.return_value = mock_detector_instance
        detection_result = DetectionResult(
            keyword_found="all tests passed",
            confidence=92,
            category="test-success",
            context_snippet="all tests passed"
        )
        mock_detector_instance.detect.return_value = detection_result

        mock_updater_instance = Mock()
        mock_updater_class.return_value = mock_updater_instance
        update_result = UpdateResult(
            updated=True,
            todo_id="task-999",
            old_status="in_progress",
            new_status="completed",
            confidence=92,
            detected_keyword="all tests passed",
            reason=None
        )
        mock_updater_instance.update_todo_from_detection.return_value = update_result

        hook = ActionItemHook(automation_hub=mock_hub, test_mode=True)

        real_pytest_output = """
============================= test session starts ==============================
platform linux -- Python 3.10.0, pytest-7.0.0
collected 15 items

tests/test_action_item_hook.py .......                                  [ 46%]
tests/test_keyword_detector.py ........                                 [ 100%]

============================== 15 passed in 0.42s ===============================
All tests passed! ✅ passing
"""

        # Act
        result = hook.handle_tool_output("bash", real_pytest_output)

        # Assert
        assert result.action_taken is True
        assert result.keyword_found == "all tests passed"
        assert result.confidence == 92


class TestWriteToolOutput:
    """Test with write tool outputs"""

    @patch('tools_db.tools.action_item_hook.KeywordDetector')
    @patch('tools_db.tools.action_item_hook.TodoUpdater')
    def test_write_tool_file_creation(self, mock_updater_class, mock_detector_class):
        """Test with write tool creating new files"""
        # Arrange
        mock_hub = Mock()
        mock_hub.store_event.return_value = 128

        mock_detector_instance = Mock()
        mock_detector_class.return_value = mock_detector_instance
        detection_result = DetectionResult(
            keyword_found="created",
            confidence=85,
            category="file-created",
            context_snippet="File created"
        )
        mock_detector_instance.detect.return_value = detection_result

        mock_updater_instance = Mock()
        mock_updater_class.return_value = mock_updater_instance
        update_result = UpdateResult(
            updated=True,
            todo_id="task-111",
            old_status="in_progress",
            new_status="completed",
            confidence=85,
            detected_keyword="created",
            reason=None
        )
        mock_updater_instance.update_todo_from_detection.return_value = update_result

        hook = ActionItemHook(automation_hub=mock_hub, test_mode=True)

        # Act
        result = hook.handle_tool_output("write", "File /path/to/action_item_hook.py created")

        # Assert
        assert result.action_taken is True
        assert result.tool_name == "write"
        assert result.keyword_found == "created"


class TestHookResultStructure:
    """Test that HookResult has all required fields"""

    @patch('tools_db.tools.action_item_hook.KeywordDetector')
    @patch('tools_db.tools.action_item_hook.TodoUpdater')
    def test_hook_result_completeness(self, mock_updater_class, mock_detector_class):
        """Test that HookResult contains all required fields"""
        # Arrange
        mock_hub = Mock()
        mock_hub.store_event.return_value = 129

        mock_detector_instance = Mock()
        mock_detector_class.return_value = mock_detector_instance
        detection_result = DetectionResult(
            keyword_found="git commit",
            confidence=95,
            category="commit-related",
            context_snippet="git commit"
        )
        mock_detector_instance.detect.return_value = detection_result

        mock_updater_instance = Mock()
        mock_updater_class.return_value = mock_updater_instance
        update_result = UpdateResult(
            updated=True,
            todo_id="task-200",
            old_status="in_progress",
            new_status="completed",
            confidence=95,
            detected_keyword="git commit",
            reason=None
        )
        mock_updater_instance.update_todo_from_detection.return_value = update_result

        hook = ActionItemHook(automation_hub=mock_hub, test_mode=True)

        # Act
        result = hook.handle_tool_output("bash", "git commit -m 'test'")

        # Assert - all fields present
        assert hasattr(result, 'action_taken')
        assert hasattr(result, 'tool_name')
        assert hasattr(result, 'keyword_found')
        assert hasattr(result, 'confidence')
        assert hasattr(result, 'todo_updated')
        assert hasattr(result, 'todo_id')
        assert hasattr(result, 'new_status')
        assert hasattr(result, 'reason')
        assert hasattr(result, 'event_id')

        # All should be set appropriately
        assert result.action_taken is True
        assert result.tool_name == "bash"
        assert result.keyword_found == "git commit"
        assert result.confidence == 95
        assert result.todo_updated is True
        assert result.todo_id == "task-200"
        assert result.new_status == "completed"
        assert result.reason == "updated_successfully"
        assert result.event_id == 129


class TestMultipleRapidExecutions:
    """Test that multiple tool executions in rapid sequence work independently"""

    @patch('tools_db.tools.action_item_hook.KeywordDetector')
    @patch('tools_db.tools.action_item_hook.TodoUpdater')
    def test_multiple_tool_executions_independent(self, mock_updater_class, mock_detector_class):
        """Test that rapid tool executions don't interfere with each other"""
        # Arrange
        mock_hub = Mock()
        mock_hub.store_event.side_effect = [130, 131, 132]  # Three event IDs

        mock_detector_instance = Mock()
        mock_detector_class.return_value = mock_detector_instance

        mock_updater_instance = Mock()
        mock_updater_class.return_value = mock_updater_instance

        hook = ActionItemHook(automation_hub=mock_hub, test_mode=True)

        # Setup different results for different calls
        detection_results = [
            DetectionResult("git commit", 95, "commit-related", "git commit"),
            DetectionResult("deployed", 88, "deployment", "deployed"),
            None,  # No detection
        ]
        mock_detector_instance.detect.side_effect = detection_results

        update_results = [
            UpdateResult(True, "task-1", "in_progress", "completed", 95, "git commit", None),
            UpdateResult(True, "task-2", "in_progress", "pending_review", 88, "deployed", None),
        ]
        mock_updater_instance.update_todo_from_detection.side_effect = update_results

        # Act - Execute 3 tools in sequence
        result1 = hook.handle_tool_output("bash", "git commit -m 'feat'")
        result2 = hook.handle_tool_output("bash", "deployed successfully")
        result3 = hook.handle_tool_output("bash", "some random output")

        # Assert - Each executes independently
        assert result1.action_taken is True
        assert result1.todo_id == "task-1"
        assert result1.event_id == 130

        assert result2.action_taken is True
        assert result2.todo_id == "task-2"
        assert result2.new_status == "pending_review"
        assert result2.event_id == 131

        assert result3.action_taken is False
        assert result3.keyword_found is None
        assert result3.reason == "no_keywords_found"


class TestUnsupportedToolsSkipped:
    """Test that unsupported tools are properly skipped"""

    def test_unsupported_tool_skip_processing(self):
        """Test that unsupported tool names return skip reason"""
        hook = ActionItemHook(automation_hub=Mock(), test_mode=True)

        # Act
        result = hook.handle_tool_output("browser_click", "Clicked button")

        # Assert
        assert result is not None
        assert result.action_taken is False
        assert result.tool_name == "browser_click"
        assert result.reason == "unsupported_tool"


class TestDetectionEventCreation:
    """Test _create_detection_event helper method"""

    def test_create_detection_event_structure(self):
        """Test that detection events have correct structure"""
        mock_hub = Mock()
        hook = ActionItemHook(automation_hub=mock_hub, test_mode=True)

        detection = DetectionResult(
            keyword_found="git commit",
            confidence=95,
            category="commit-related",
            context_snippet="git commit -m"
        )

        update_result = UpdateResult(
            updated=True,
            todo_id="task-123",
            old_status="in_progress",
            new_status="completed",
            confidence=95,
            detected_keyword="git commit",
            reason=None
        )

        # Act
        event = hook._create_detection_event(detection, update_result, "bash")

        # Assert
        assert isinstance(event, AutomationEvent)
        assert event.event_type == "action_item_completed"
        assert event.status == "success"
        assert event.detected_from == "hook"
        assert event.evidence is not None
        assert "tool_name" in event.evidence
        assert event.evidence["tool_name"] == "bash"
        assert event.evidence["detected_keyword"] == "git commit"
        assert event.evidence["confidence"] == 95
        assert event.evidence["todo_id"] == "task-123"


class TestCreateDetectionEventPendingReview:
    """Test event creation for pending_review status"""

    def test_create_detection_event_pending_review(self):
        """Test that pending_review updates create appropriate events"""
        mock_hub = Mock()
        hook = ActionItemHook(automation_hub=mock_hub, test_mode=True)

        detection = DetectionResult(
            keyword_found="fixed",
            confidence=72,
            category="bug-fixed",
            context_snippet="bug fixed"
        )

        update_result = UpdateResult(
            updated=True,
            todo_id="task-456",
            old_status="in_progress",
            new_status="pending_review",
            confidence=72,
            detected_keyword="fixed",
            reason=None
        )

        # Act
        event = hook._create_detection_event(detection, update_result, "edit")

        # Assert
        assert event.event_type == "action_item_pending_review"
        assert event.status == "pending_review"


class TestEmptyToolOutput:
    """Test edge case of empty tool output"""

    @patch('tools_db.tools.action_item_hook.KeywordDetector')
    def test_empty_tool_output_skipped(self, mock_detector_class):
        """Test that empty tool output is handled gracefully"""
        mock_hub = Mock()
        mock_detector_instance = Mock()
        mock_detector_class.return_value = mock_detector_instance
        mock_detector_instance.detect.return_value = None

        hook = ActionItemHook(automation_hub=mock_hub, test_mode=True)

        # Act
        result = hook.handle_tool_output("bash", "")

        # Assert
        assert result.action_taken is False
        assert result.reason == "no_keywords_found"


class TestToolOutputWithOnlyWhitespace:
    """Test edge case of whitespace-only tool output"""

    @patch('tools_db.tools.action_item_hook.KeywordDetector')
    def test_whitespace_tool_output_skipped(self, mock_detector_class):
        """Test that whitespace-only output is handled"""
        mock_hub = Mock()
        mock_detector_instance = Mock()
        mock_detector_class.return_value = mock_detector_instance
        mock_detector_instance.detect.return_value = None

        hook = ActionItemHook(automation_hub=mock_hub, test_mode=True)

        # Act
        result = hook.handle_tool_output("bash", "   \n\t  ")

        # Assert
        assert result.action_taken is False
