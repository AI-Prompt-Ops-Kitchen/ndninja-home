"""Mock adapter for testing and development"""

import time
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from adapters.base import CLIAgentAdapter, BenchmarkResult
from recording_manager import RecordingManager


class MockAdapter(CLIAgentAdapter):
    """Mock CLI agent adapter for testing

    Simulates agent behavior without actually calling external CLIs.
    Useful for testing the benchmark infrastructure.
    """

    def __init__(
        self,
        simulate_success: bool = True,
        simulate_wall_time: float = 1.0,
        simulate_cost: float = 0.01,
        simulate_retries: int = None,
        simulate_tool_calls: int = 10,
        simulate_error_recovery: bool = False
    ):
        """Initialize mock adapter

        Args:
            simulate_success: Whether to simulate successful execution
            simulate_wall_time: Simulated execution time in seconds
            simulate_cost: Simulated API cost in USD
            simulate_retries: Number of retries to simulate (defaults based on success)
            simulate_tool_calls: Number of tool calls to simulate
            simulate_error_recovery: Whether to simulate error recovery
        """
        self.simulate_success = simulate_success
        self.simulate_wall_time = simulate_wall_time
        self.simulate_cost = simulate_cost
        # Default retries: 0 for success, 3 for failure
        if simulate_retries is None:
            self.simulate_retries = 0 if simulate_success else 3
        else:
            self.simulate_retries = simulate_retries
        self.simulate_tool_calls = simulate_tool_calls
        self.simulate_error_recovery = simulate_error_recovery
        self.task_dir = None
        self.recorder = RecordingManager()

    def setup(self, task_dir: str) -> None:
        """Prepare mock environment"""
        self.task_dir = task_dir

    def execute_task(self, prompt: str, timeout: int) -> BenchmarkResult:
        """Simulate task execution"""
        # Simulate some work
        time.sleep(min(0.1, self.simulate_wall_time))

        # Generate mock recording path
        recording_path = self.recorder.get_recording_path(
            agent="mock",
            task=Path(self.task_dir).name if self.task_dir else "unknown"
        )

        # Create empty recording file
        Path(recording_path).touch()

        return BenchmarkResult(
            success=self.simulate_success,
            wall_time=self.simulate_wall_time,
            token_count={"input": 100, "output": 50},
            cost=self.simulate_cost,
            retries=self.simulate_retries,
            tool_calls=self.simulate_tool_calls,
            error_recovered=self.simulate_error_recovery,
            generated_files=["mock_output.py"],
            logs=f"Mock execution log\nPrompt: {prompt[:50]}...",
            recording_path=recording_path
        )

    def cleanup(self) -> None:
        """Clean up mock resources"""
        # Clean up mock recording files
        if self.task_dir:
            for cast_file in Path(self.recorder.output_dir).glob("mock_*.cast"):
                cast_file.unlink(missing_ok=True)
