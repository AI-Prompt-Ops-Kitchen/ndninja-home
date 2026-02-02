"""Kimi CLI adapter"""

import subprocess
import time
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from adapters.base import CLIAgentAdapter, BenchmarkResult
from recording_manager import RecordingManager


class KimiAdapter(CLIAgentAdapter):
    """Adapter for Kimi CLI (kimi-cli)

    Documentation: https://github.com/MoonshotAI/kimi-cli
    """

    def __init__(self, api_key: str = None):
        """Initialize Kimi CLI adapter

        Args:
            api_key: Optional API key (uses NVIDIA free tier if not provided)
        """
        self.api_key = api_key
        self.task_dir = None
        self.recorder = RecordingManager()
        self.process = None

    def setup(self, task_dir: str) -> None:
        """Prepare Kimi CLI environment

        Args:
            task_dir: Path to task directory
        """
        self.task_dir = task_dir

    def execute_task(self, prompt: str, timeout: int) -> BenchmarkResult:
        """Execute task with Kimi CLI

        Args:
            prompt: Task description
            timeout: Maximum execution time in seconds

        Returns:
            BenchmarkResult with metrics

        Note:
            This is a stub implementation. Actual implementation requires:
            1. Installing kimi-cli: pip install kimi-cli
            2. Configuring API credentials
            3. Understanding Kimi's stdin/stdout protocol
            4. Parsing output for token counts, retries, tool calls
        """
        # TODO: Implement actual Kimi CLI execution
        # For now, return a stub result
        raise NotImplementedError(
            "Kimi adapter not yet implemented. "
            "Install kimi-cli and configure API access first. "
            "See: https://github.com/MoonshotAI/kimi-cli"
        )

    def cleanup(self) -> None:
        """Clean up Kimi CLI process"""
        if self.process:
            self.process.terminate()
            self.process.wait(timeout=5)

    @staticmethod
    def check_available() -> bool:
        """Check if Kimi CLI is installed and available

        Returns:
            True if kimi-cli is available, False otherwise
        """
        try:
            result = subprocess.run(
                ["kimi", "--version"],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False
