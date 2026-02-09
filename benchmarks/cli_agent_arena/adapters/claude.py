"""Claude Code adapter"""

import subprocess
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from adapters.base import CLIAgentAdapter, BenchmarkResult
from recording_manager import RecordingManager


class ClaudeCodeAdapter(CLIAgentAdapter):
    """Adapter for Claude Code CLI

    Uses the claude command-line tool (this tool we're using right now!)
    """

    def __init__(self, api_key: str = None):
        """Initialize Claude Code adapter

        Args:
            api_key: Optional Anthropic API key (uses environment if not provided)
        """
        self.api_key = api_key
        self.task_dir = None
        self.recorder = RecordingManager()
        self.process = None

    def setup(self, task_dir: str) -> None:
        """Prepare Claude Code environment

        Args:
            task_dir: Path to task directory
        """
        self.task_dir = task_dir

    def execute_task(self, prompt: str, timeout: int) -> BenchmarkResult:
        """Execute task with Claude Code

        Args:
            prompt: Task description
            timeout: Maximum execution time in seconds

        Returns:
            BenchmarkResult with metrics

        Note:
            This is a stub implementation. Actual implementation requires:
            1. Spawning claude CLI in task directory
            2. Sending prompt via stdin or file
            3. Monitoring output for tool usage, retries
            4. Extracting token counts from conversation
            5. Wrapping execution in asciinema
        """
        # TODO: Implement actual Claude Code execution
        # Challenge: We're INSIDE Claude Code right now!
        # Need to spawn a separate Claude Code process
        raise NotImplementedError(
            "Claude Code adapter not yet implemented. "
            "Requires spawning separate claude process with API."
        )

    def cleanup(self) -> None:
        """Clean up Claude Code process"""
        if self.process:
            self.process.terminate()
            self.process.wait(timeout=5)

    @staticmethod
    def check_available() -> bool:
        """Check if Claude Code is installed and available

        Returns:
            True if claude is available, False otherwise
        """
        try:
            result = subprocess.run(
                ["claude", "--version"],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False
