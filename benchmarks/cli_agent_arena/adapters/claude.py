"""Claude Code adapter"""

import subprocess
import time
import os
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from adapters.base import CLIAgentAdapter, BenchmarkResult
from recording_manager import RecordingManager
from adapters.parsers.claude_parser import ClaudeParser
from quality.analyzer import QualityAnalyzer


class ClaudeCodeAdapter(CLIAgentAdapter):
    """Adapter for Claude Code CLI

    Uses the claude command-line tool
    """

    def __init__(self, api_key: str = None, model: str = "sonnet"):
        """Initialize Claude Code adapter

        Args:
            api_key: Optional Anthropic API key (uses environment if not provided)
            model: Model to use (sonnet, opus, haiku)
        """
        self.api_key = api_key
        self.model = model
        self.task_dir = None
        self.recorder = RecordingManager()
        self.parser = ClaudeParser()
        self.quality_analyzer = QualityAnalyzer()
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
        """
        # Generate recording path
        task_name = Path(self.task_dir).name if self.task_dir else "unknown"
        recording_path = self.recorder.get_recording_path("claude", task_name)

        # Write prompt to task file
        if self.task_dir:
            task_file = Path(self.task_dir) / "TASK.md"
            task_file.write_text(prompt)

        # Track time
        start_time = time.time()

        # Build Claude CLI command
        cmd = ["claude"]
        if self.api_key:
            cmd.extend(["--api-key", self.api_key])
        if self.model:
            cmd.extend(["--model", self.model])

        # Prepare environment
        env = os.environ.copy()
        if self.task_dir:
            os.chdir(self.task_dir)

        try:
            # Execute with asciinema recording if available
            if self.recorder.check_asciinema_available():
                result = subprocess.run(
                    ["asciinema", "rec", "-c", " ".join(cmd), recording_path],
                    input=prompt,
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    env=env,
                )
            else:
                # Run without recording
                result = subprocess.run(
                    cmd,
                    input=prompt,
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    env=env,
                )
                recording_path = ""

            wall_time = time.time() - start_time
            stdout = result.stdout
            stderr = result.stderr
            success = result.returncode == 0

            # Parse metrics from output
            metrics = self.parser.extract_metrics(stdout, stderr, result.returncode)

            # Find generated files
            generated_files = []
            if self.task_dir:
                task_path = Path(self.task_dir)
                for file in task_path.rglob("*.py"):
                    if file.name != "TASK.md":
                        generated_files.append(str(file.relative_to(task_path)))

            # Analyze code quality if task succeeded
            quality_score = 0.0
            if success and generated_files:
                quality_score = self.quality_analyzer.analyze(
                    [str(Path(self.task_dir) / f) for f in generated_files]
                )

            return BenchmarkResult(
                success=success,
                wall_time=wall_time,
                token_count=metrics["token_count"],
                cost=metrics["cost"],
                retries=metrics["retries"],
                tool_calls=metrics["tool_calls"],
                error_recovered=metrics["error_recovered"],
                generated_files=generated_files,
                logs=stdout + "\n" + stderr,
                recording_path=recording_path,
                quality_score=quality_score,
            )

        except subprocess.TimeoutExpired:
            wall_time = time.time() - start_time
            return BenchmarkResult(
                success=False,
                wall_time=wall_time,
                token_count={"input": 0, "output": 0},
                cost=0.0,
                retries=0,
                tool_calls=0,
                error_recovered=False,
                generated_files=[],
                logs=f"Execution timed out after {timeout}s",
                recording_path="",
            )

        except Exception as e:
            wall_time = time.time() - start_time
            return BenchmarkResult(
                success=False,
                wall_time=wall_time,
                token_count={"input": 0, "output": 0},
                cost=0.0,
                retries=0,
                tool_calls=0,
                error_recovered=False,
                generated_files=[],
                logs=f"Error: {str(e)}",
                recording_path="",
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
