"""
PostToolUse hook for action item completion tracking.

This module orchestrates KeywordDetector and TodoUpdater to automatically
detect and update todos based on tool outputs. It serves as the main entry
point for the PostToolUse hook event.

Workflow:
1. Tool executes (Write/Bash/Edit)
2. PostToolUse event fires with tool output
3. ActionItemHook.handle_tool_output(tool_name, tool_output)
4. KeywordDetector.detect(tool_output)
5. If keyword found: TodoUpdater.update_todo_from_detection(detection)
6. AutomationHub.store_event(event) - Log action for audit trail
7. Return event result with status (detected/updated/no_action)
"""

from typing import Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime, timezone

from tools_db.tools.keyword_detector import KeywordDetector, DetectionResult
from tools_db.tools.todo_updater import TodoUpdater, UpdateResult
from tools_db.models import AutomationEvent


@dataclass
class HookResult:
    """Result structure for PostToolUse hook execution"""
    action_taken: bool              # True if detection + update occurred
    tool_name: str                  # Name of the tool that executed
    keyword_found: Optional[str]    # Keyword that was detected
    confidence: Optional[int]       # Confidence score (0-100)
    todo_updated: bool              # True if todo was actually updated
    todo_id: Optional[str]          # ID of updated todo (None if no-op)
    new_status: Optional[str]       # New status of todo
    reason: str                     # "no_keywords_found", "low_confidence", "unsupported_tool", "no_matching_todos", "updated_successfully", etc.
    event_id: Optional[int]         # Database event ID for audit trail


class ActionItemHook:
    """
    PostToolUse hook that analyzes tool outputs for completion keywords
    and auto-updates todos based on confidence scoring.

    Supported tools:
    - bash: Git commits, test results, deployment output
    - write: File creation events
    - edit: Code changes (less reliable, use conservatively)

    Confidence thresholds:
    - ≥80%: Auto-update todo to "completed"
    - 60-80%: Mark todo as "pending_review"
    - <60%: Skip (false positive prevention)
    """

    # Tools to analyze
    SUPPORTED_TOOLS = {"bash", "write", "edit"}

    def __init__(self, automation_hub: Optional[Any] = None, test_mode: bool = False):
        """
        Initialize ActionItemHook.

        Args:
            automation_hub: AutomationHub instance for storing events
            test_mode: If True, run in test mode with in-memory event storage
        """
        self.automation_hub = automation_hub
        self.test_mode = test_mode
        self.keyword_detector = KeywordDetector()
        self.todo_updater = TodoUpdater()

    def handle_tool_output(self, tool_name: str, tool_output: str) -> HookResult:
        """
        Main hook entry point. Analyzes tool output for completion keywords
        and orchestrates detection and update workflow.

        Args:
            tool_name: Name of the tool that executed (bash, write, edit, etc.)
            tool_output: The output string from the tool execution

        Returns:
            HookResult with action status and audit trail info
        """
        try:
            # Check if this tool should be processed
            if not self._should_process_tool(tool_name):
                return HookResult(
                    action_taken=False,
                    tool_name=tool_name,
                    keyword_found=None,
                    confidence=None,
                    todo_updated=False,
                    todo_id=None,
                    new_status=None,
                    reason="unsupported_tool",
                    event_id=None
                )

            # Skip empty/whitespace-only output
            if not tool_output or not tool_output.strip():
                return HookResult(
                    action_taken=False,
                    tool_name=tool_name,
                    keyword_found=None,
                    confidence=None,
                    todo_updated=False,
                    todo_id=None,
                    new_status=None,
                    reason="no_keywords_found",
                    event_id=None
                )

            # Step 1: Detect keywords in tool output
            detection = self.keyword_detector.detect(tool_output)

            if detection is None:
                return HookResult(
                    action_taken=False,
                    tool_name=tool_name,
                    keyword_found=None,
                    confidence=None,
                    todo_updated=False,
                    todo_id=None,
                    new_status=None,
                    reason="no_keywords_found",
                    event_id=None
                )

            # Check confidence threshold
            if detection.confidence < 60:
                return HookResult(
                    action_taken=False,
                    tool_name=tool_name,
                    keyword_found=detection.keyword_found,
                    confidence=detection.confidence,
                    todo_updated=False,
                    todo_id=None,
                    new_status=None,
                    reason="low_confidence",
                    event_id=None
                )

            # Step 2: Update todo based on detection
            update_result = self.todo_updater.update_todo_from_detection(detection)

            # Step 3: Create and store event
            event = self._create_detection_event(detection, update_result, tool_name)
            event_id = self._store_event(event)

            # Step 4: Return result
            if update_result.updated:
                return HookResult(
                    action_taken=True,
                    tool_name=tool_name,
                    keyword_found=detection.keyword_found,
                    confidence=detection.confidence,
                    todo_updated=True,
                    todo_id=update_result.todo_id,
                    new_status=update_result.new_status,
                    reason="updated_successfully",
                    event_id=event_id
                )
            else:
                # Detection succeeded but update did not
                return HookResult(
                    action_taken=False,
                    tool_name=tool_name,
                    keyword_found=detection.keyword_found,
                    confidence=detection.confidence,
                    todo_updated=False,
                    todo_id=None,
                    new_status=None,
                    reason=update_result.reason or "no_matching_todos",
                    event_id=event_id
                )

        except Exception as e:
            # Graceful error handling
            return HookResult(
                action_taken=False,
                tool_name=tool_name,
                keyword_found=None,
                confidence=None,
                todo_updated=False,
                todo_id=None,
                new_status=None,
                reason=f"error: {str(e)}",
                event_id=None
            )

    def _should_process_tool(self, tool_name: str) -> bool:
        """
        Check if tool output should be analyzed.

        Args:
            tool_name: Name of the tool

        Returns:
            True if tool should be processed, False otherwise
        """
        return tool_name in self.SUPPORTED_TOOLS

    def _create_detection_event(
        self,
        detection: DetectionResult,
        update_result: UpdateResult,
        tool_name: str
    ) -> AutomationEvent:
        """
        Create an AutomationEvent for audit trail logging.

        Args:
            detection: The keyword detection result
            update_result: The todo update result
            tool_name: The tool that executed

        Returns:
            AutomationEvent with evidence and metadata
        """
        # Determine event type and status based on update result
        if not update_result.updated:
            event_type = "no_action_taken"
            status = "skipped"
        elif update_result.new_status == "completed":
            event_type = "action_item_completed"
            status = "success"
        elif update_result.new_status == "pending_review":
            event_type = "action_item_pending_review"
            status = "pending_review"
        else:
            event_type = "action_item_updated"
            status = "success"

        # Build evidence dictionary
        evidence: Dict[str, Any] = {
            "tool_name": tool_name,
            "detected_keyword": detection.keyword_found,
            "keyword_category": detection.category,
            "confidence": detection.confidence,
            "context_snippet": detection.context_snippet,
        }

        # Add todo update info if available
        if update_result.updated:
            evidence["todo_id"] = update_result.todo_id
            evidence["old_status"] = update_result.old_status
            evidence["new_status"] = update_result.new_status
        else:
            evidence["update_reason"] = update_result.reason

        # Create the event
        event = AutomationEvent(
            event_type=event_type,
            project_id="tier1-automation",  # Could be made configurable
            status=status,
            evidence=evidence,
            detected_from="hook",
            metadata={
                "hook_type": "PostToolUse",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )

        return event

    def _store_event(self, event: AutomationEvent) -> Optional[int]:
        """
        Store event to automation_events table for audit trail.

        Args:
            event: AutomationEvent to store

        Returns:
            Event ID if stored successfully, None if storage failed
        """
        if self.automation_hub is None:
            return None

        try:
            event_id = self.automation_hub.store_event(event)
            return event_id
        except Exception as e:
            # Graceful degradation - don't crash if storage fails
            if not self.test_mode:
                print(f"Warning: Failed to store automation event: {e}")
            return None
