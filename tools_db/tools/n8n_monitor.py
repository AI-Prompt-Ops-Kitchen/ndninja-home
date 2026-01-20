"""
N8n Task Monitor - Detects n8n task failures and logs them for fallback routing.

This module provides real-time monitoring of n8n task execution, detects failures
(403 Unauthorized, 504 Gateway Timeout, timeout errors >30s, webhook errors),
extracts task metadata, and logs failures to the automation_events table for
audit trail and fallback routing.

Failure Detection:
- 403 Unauthorized: Authentication failure (expired token, permission issue)
- 504 Gateway Timeout: n8n service temporarily unavailable
- Execution Timeout: Task hangs for >30 seconds
- Webhook Error: n8n failed to reach external webhook
- Unknown Error: Any response containing error/failed keywords

Workflow:
1. Register task for monitoring via register_task()
2. Task executes in n8n
3. Call report_result() with status_code and response
4. Monitor detects failure pattern if present
5. If failure: Extract metadata, log to automation_events
6. Return MonitorResult for fallback routing decision
"""

from typing import Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
import uuid

from tools_db.models import AutomationEvent


class FailureType(Enum):
    """Enumeration of n8n failure types"""
    AUTH_FAILURE = "403_unauthorized"
    GATEWAY_TIMEOUT = "504_gateway_timeout"
    EXECUTION_TIMEOUT = "execution_timeout"
    WEBHOOK_FAILURE = "webhook_error"
    UNKNOWN_ERROR = "unknown_error"
    NO_FAILURE = "success"


@dataclass
class MonitorResult:
    """Result structure for task monitoring"""
    failure_detected: bool              # True if failure pattern detected
    failure_type: Optional[FailureType] # Type of failure if detected
    task_id: str                        # Original task ID
    workflow_name: str                  # Original workflow name
    status_code: Optional[int]          # HTTP status code
    duration_seconds: float             # Task execution duration
    reason: str                         # Explanation of failure or "success"
    event_id: Optional[int]             # automation_events table ID


class N8nMonitor:
    """
    Monitor for n8n task execution with failure detection and logging.

    Detects common n8n failures and logs them to automation_events for
    audit trail and fallback routing decisions.
    """

    def __init__(self, automation_hub: Optional[Any] = None, test_mode: bool = False):
        """
        Initialize N8nMonitor.

        Args:
            automation_hub: AutomationHub instance for storing events
            test_mode: If True, run in test mode with in-memory event storage
        """
        self.automation_hub = automation_hub
        self.test_mode = test_mode
        self._task_registry: Dict[str, Dict[str, Any]] = {}
        self._memory_events = []  # For test mode

    def register_task(self, task_id: str, workflow_name: str, input_params: Dict) -> str:
        """
        Register n8n task for monitoring.

        Args:
            task_id: Unique task identifier (e.g., "video-assembly")
            workflow_name: n8n workflow name
            input_params: Task input parameters for metadata extraction

        Returns:
            Monitor ID (string) to use when reporting results
        """
        monitor_id = str(uuid.uuid4())
        self._task_registry[monitor_id] = {
            "task_id": task_id,
            "workflow_name": workflow_name,
            "input_params": input_params,
            "registered_at": datetime.now(timezone.utc)
        }
        return monitor_id

    def report_result(
        self,
        monitor_id: str,
        status_code: Optional[int],
        response: str,
        duration_seconds: float
    ) -> MonitorResult:
        """
        Report task result (success or failure).

        Detects failure patterns, extracts metadata, and logs to automation_events
        if failure detected.

        Args:
            monitor_id: Monitor ID from register_task()
            status_code: HTTP status code from n8n response
            response: Response body/message from n8n
            duration_seconds: Task execution duration in seconds

        Returns:
            MonitorResult with failure detection and logging info
        """
        # Get registered task info or create implicit registration
        task_info = self._task_registry.get(monitor_id)
        if not task_info:
            # Implicit registration for tasks reported without prior registration
            task_info = {
                "task_id": "unknown",
                "workflow_name": "unknown",
                "input_params": {},
                "registered_at": datetime.now(timezone.utc)
            }
            self._task_registry[monitor_id] = task_info

        task_id = task_info["task_id"]
        workflow_name = task_info["workflow_name"]
        input_params = task_info["input_params"]

        # Detect failure pattern
        failure_type = self._detect_failure_pattern(status_code, response, duration_seconds)

        # Extract metadata
        metadata = self._extract_task_metadata(task_id, workflow_name, input_params)

        # Prepare result
        failure_detected = failure_type != FailureType.NO_FAILURE
        reason = self._get_failure_reason(failure_type, status_code, duration_seconds)

        # Log to automation_events if failure detected
        event_id = None
        if failure_detected and self.automation_hub:
            event_id = self._log_failure_event(
                task_id,
                workflow_name,
                failure_type,
                status_code,
                response,
                duration_seconds,
                metadata
            )

        return MonitorResult(
            failure_detected=failure_detected,
            failure_type=failure_type,
            task_id=task_id,
            workflow_name=workflow_name,
            status_code=status_code,
            duration_seconds=duration_seconds,
            reason=reason,
            event_id=event_id
        )

    def _detect_failure_pattern(
        self,
        status_code: Optional[int],
        response: str,
        duration_seconds: float
    ) -> FailureType:
        """
        Check for failure patterns in response.

        Priority:
        1. Check execution timeout (duration > 30s)
        2. Check HTTP status code for known failures
        3. Check response content for failure keywords

        Args:
            status_code: HTTP status code
            response: Response body
            duration_seconds: Task execution duration

        Returns:
            FailureType indicating detected failure or NO_FAILURE
        """
        # Normalize response
        if not response:
            response = ""

        response_lower = response.lower().strip() if response else ""

        # Check 1: Execution timeout (duration > 30 seconds)
        if duration_seconds > 30.0:
            return FailureType.EXECUTION_TIMEOUT

        # Check 2: Status code 403
        if status_code == 403:
            return FailureType.AUTH_FAILURE

        # Check 3: Status code 504
        if status_code == 504:
            return FailureType.GATEWAY_TIMEOUT

        # Check 4: Response content - Auth failure patterns
        auth_keywords = ["unauthorized", "invalid token", "permission", "auth failed"]
        if any(keyword in response_lower for keyword in auth_keywords):
            return FailureType.AUTH_FAILURE

        # Check 5: Response content - Gateway timeout patterns
        gateway_keywords = ["gateway", "timeout", "unavailable", "service unavailable"]
        if any(keyword in response_lower for keyword in gateway_keywords):
            return FailureType.GATEWAY_TIMEOUT

        # Check 6: Response content - Webhook failure patterns
        webhook_keywords = ["webhook", "external", "connection refused", "connection failed"]
        if any(keyword in response_lower for keyword in webhook_keywords):
            return FailureType.WEBHOOK_FAILURE

        # Check 7: Response content - Unknown error patterns
        error_keywords = ["error:", "error ", "failed", "failed:"]
        if any(keyword in response_lower for keyword in error_keywords):
            return FailureType.UNKNOWN_ERROR

        # No failure detected
        return FailureType.NO_FAILURE

    def _extract_task_metadata(
        self,
        task_id: str,
        workflow_name: str,
        input_params: Dict
    ) -> Dict[str, Any]:
        """
        Extract task metadata for logging and debugging.

        Args:
            task_id: Task identifier
            workflow_name: Workflow name
            input_params: Input parameters

        Returns:
            Dictionary with extracted metadata
        """
        return {
            "task_id": task_id,
            "workflow_name": workflow_name,
            "input_params": input_params,
            "extracted_at": datetime.now(timezone.utc).isoformat()
        }

    def _get_failure_reason(
        self,
        failure_type: FailureType,
        status_code: Optional[int],
        duration_seconds: float
    ) -> str:
        """
        Generate human-readable reason for failure or success.

        Args:
            failure_type: Detected failure type
            status_code: HTTP status code
            duration_seconds: Task duration

        Returns:
            String explanation of failure or success
        """
        if failure_type == FailureType.NO_FAILURE:
            return f"Task completed successfully in {duration_seconds:.2f}s"
        elif failure_type == FailureType.AUTH_FAILURE:
            return f"Authentication failure (403 Unauthorized)"
        elif failure_type == FailureType.GATEWAY_TIMEOUT:
            return f"Gateway timeout - n8n service unavailable (504)"
        elif failure_type == FailureType.EXECUTION_TIMEOUT:
            return f"Task execution timeout - exceeded 30s threshold ({duration_seconds:.2f}s)"
        elif failure_type == FailureType.WEBHOOK_FAILURE:
            return f"Webhook error - failed to reach external service"
        elif failure_type == FailureType.UNKNOWN_ERROR:
            return f"Unknown error occurred during task execution"
        else:
            return "Unknown status"

    def _log_failure_event(
        self,
        task_id: str,
        workflow_name: str,
        failure_type: FailureType,
        status_code: Optional[int],
        response: str,
        duration_seconds: float,
        metadata: Dict[str, Any]
    ) -> Optional[int]:
        """
        Log failure event to automation_events table.

        Args:
            task_id: Task identifier
            workflow_name: Workflow name
            failure_type: Type of failure detected
            status_code: HTTP status code
            response: Response body/message
            duration_seconds: Execution duration
            metadata: Extracted task metadata

        Returns:
            Event ID if logged, None if hub unavailable
        """
        if not self.automation_hub:
            return None

        # Extract snippet from response (truncate if very long)
        response_snippet = response[:200] if response else ""

        # Prepare evidence
        evidence = {
            "task_id": task_id,
            "workflow_name": workflow_name,
            "failure_type": failure_type.value,
            "status_code": status_code,
            "duration_seconds": duration_seconds,
            "response_snippet": response_snippet,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        # Prepare metadata
        hub_metadata = {
            "monitor_type": "n8n",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "can_fallback": True,  # Can attempt fallback routing
            "extracted_metadata": metadata
        }

        # Create event
        event = AutomationEvent(
            event_type="n8n_failure_detected",
            project_id="n8n",
            status="failed",
            evidence=evidence,
            detected_from="monitor",
            metadata=hub_metadata
        )

        # Store event
        return self.automation_hub.store_event(event)
