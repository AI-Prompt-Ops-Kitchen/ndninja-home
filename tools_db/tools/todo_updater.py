"""
Todo updater for action item progress tracking.

Matches keyword detection results to in-memory todos and auto-updates
their status based on confidence scoring thresholds.
"""

from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from datetime import datetime
from tools_db.tools.keyword_detector import DetectionResult


@dataclass
class UpdateResult:
    """Result of a todo update operation"""
    updated: bool              # Whether todo was actually updated
    todo_id: Optional[str] = None   # ID of updated todo (None if no-op)
    old_status: Optional[str] = None     # Previous status
    new_status: Optional[str] = None     # New status
    confidence: Optional[int] = None     # Detection confidence that triggered update
    detected_keyword: Optional[str] = None   # Keyword that matched
    reason: Optional[str] = None   # Reason for result (e.g., "low_confidence", "no_matching_todos")


class TodoUpdater:
    """
    Updates todo status based on keyword detection results.

    Implements the following logic:
    1. If confidence ≥ 80%: Auto-update todo status from "in_progress" → "completed"
    2. If confidence 60-80%: Mark as "pending_review" (user can confirm/reject)
    3. If <60%: Skip (already filtered by detector)

    Todo Matching Algorithm:
    - Match keyword categories to todo keywords
    - Only match todos currently in "in_progress" state
    - If multiple "in_progress" matches: Update the most recent
    - If no "in_progress" todos: No-op (don't update completed/pending todos)
    """

    # Mapping of keyword categories to todo keywords
    CATEGORY_KEYWORDS = {
        "commit-related": ["Implement", "Build", "Deploy", "Add", "Modify", "Update"],
        "deployment": ["Deploy", "Push", "Release", "Ship"],
        "test-success": ["Test", "Run", "Verify", "Check"],
        "bug-fixed": ["Fix", "Resolve", "Patch", "Handle"],
        "build-success": ["Build", "Compile", "Create"],
        "file-created": ["Create", "Write", "Generate", "Add"],
    }

    # Confidence thresholds
    HIGH_CONFIDENCE_THRESHOLD = 80  # Auto-update to completed
    MEDIUM_CONFIDENCE_THRESHOLD = 60  # Mark as pending_review
    LOW_CONFIDENCE_THRESHOLD = 60  # Skip (filter threshold)

    def __init__(self):
        """Initialize the TodoUpdater"""
        pass

    def update_todo_from_detection(self, detection: DetectionResult) -> UpdateResult:
        """
        Update a todo based on keyword detection results.

        Args:
            detection: DetectionResult from KeywordDetector

        Returns:
            UpdateResult with update status and audit trail
        """
        try:
            # Filter by confidence threshold
            if detection.confidence < self.LOW_CONFIDENCE_THRESHOLD:
                return UpdateResult(
                    updated=False,
                    confidence=detection.confidence,
                    detected_keyword=detection.keyword_found,
                    reason="low_confidence"
                )

            # Query memory system for current todos
            try:
                todos = self._query_memory_todos()
            except Exception as e:
                return UpdateResult(
                    updated=False,
                    confidence=detection.confidence,
                    detected_keyword=detection.keyword_found,
                    reason="memory_system_error"
                )

            # Filter to in_progress todos only
            in_progress_todos = [
                todo for todo in todos
                if todo.get('status') == 'in_progress'
            ]

            if not in_progress_todos:
                return UpdateResult(
                    updated=False,
                    confidence=detection.confidence,
                    detected_keyword=detection.keyword_found,
                    reason="no_matching_todos"
                )

            # Find most recent in_progress todo
            most_recent_todo = self._find_most_recent_todo(in_progress_todos)

            if not most_recent_todo:
                return UpdateResult(
                    updated=False,
                    confidence=detection.confidence,
                    detected_keyword=detection.keyword_found,
                    reason="no_matching_todos"
                )

            # Determine new status based on confidence threshold
            if detection.confidence >= self.HIGH_CONFIDENCE_THRESHOLD:
                new_status = "completed"
            else:  # 60-80% range
                new_status = "pending_review"

            # Update the todo in memory system
            try:
                success = self._update_memory_todo(
                    most_recent_todo['id'],
                    old_status=most_recent_todo['status'],
                    new_status=new_status,
                    detection=detection
                )

                if not success:
                    return UpdateResult(
                        updated=False,
                        confidence=detection.confidence,
                        detected_keyword=detection.keyword_found,
                        reason="update_failed"
                    )

                return UpdateResult(
                    updated=True,
                    todo_id=most_recent_todo['id'],
                    old_status=most_recent_todo['status'],
                    new_status=new_status,
                    confidence=detection.confidence,
                    detected_keyword=detection.keyword_found,
                    reason=None
                )

            except Exception as e:
                return UpdateResult(
                    updated=False,
                    confidence=detection.confidence,
                    detected_keyword=detection.keyword_found,
                    reason="update_failed"
                )

        except Exception as e:
            return UpdateResult(
                updated=False,
                confidence=detection.confidence,
                detected_keyword=detection.keyword_found,
                reason="unexpected_error"
            )

    def _query_memory_todos(self) -> List[Dict[str, Any]]:
        """
        Query memory system for current todos.

        Returns:
            List of todo dictionaries with id, title, status, created_at fields

        Raises:
            Exception: If memory system is unavailable
        """
        # This method will be mocked in tests
        # In production, this would call the claude-memory API
        # via the mcp__claude-memory__get_workspace_items tool
        raise NotImplementedError("Must be implemented or mocked in subclass")

    def _update_memory_todo(
        self,
        todo_id: str,
        old_status: str,
        new_status: str,
        detection: DetectionResult
    ) -> bool:
        """
        Update todo status in memory system.

        Args:
            todo_id: ID of the todo to update
            old_status: Previous status
            new_status: New status to set
            detection: The detection result that triggered the update

        Returns:
            True if update succeeded, False otherwise

        Raises:
            Exception: If memory system is unavailable
        """
        # This method will be mocked in tests
        # In production, this would call the claude-memory API
        # via the mcp__claude-memory__update_action_item_progress tool
        raise NotImplementedError("Must be implemented or mocked in subclass")

    def _find_most_recent_todo(self, todos: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        Find the most recently created todo from a list.

        Args:
            todos: List of todo dictionaries (must have created_at field)

        Returns:
            The todo with the most recent created_at timestamp
        """
        if not todos:
            return None

        # Sort by created_at in descending order (most recent first)
        sorted_todos = sorted(
            todos,
            key=lambda t: t.get('created_at', ''),
            reverse=True
        )

        return sorted_todos[0] if sorted_todos else None
