"""Gemini CLI adapter"""

import subprocess
import time
import os
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from adapters.base import CLIAgentAdapter, BenchmarkResult
from recording_manager import RecordingManager
from adapters.parsers.gemini_parser import GeminiParser
from quality.analyzer import QualityAnalyzer


class GeminiAdapter(CLIAgentAdapter):
    """Adapter for Google Gemini CLI (v0.27+)

    Uses the `gemini` command-line tool with `-o json` for structured output.
    """

    def __init__(self, api_key: str = None):
        """Initialize Gemini adapter

        Args:
            api_key: Optional GEMINI_API_KEY (uses environment if not provided)
        """
        self.api_key = api_key
        self.task_dir = None
        self.recorder = RecordingManager()
        self.parser = GeminiParser()
        self.quality_analyzer = QualityAnalyzer()
        self.process = None

    def setup(self, task_dir: str) -> None:
        """Prepare Gemini environment

        Args:
            task_dir: Path to task directory
        """
        self.task_dir = task_dir

    def execute_task(self, prompt: str, timeout: int) -> BenchmarkResult:
        """Execute task with Gemini CLI

        Args:
            prompt: Task description
            timeout: Maximum execution time in seconds

        Returns:
            BenchmarkResult with metrics
        """
        task_name = Path(self.task_dir).name if self.task_dir else "unknown"
        recording_path = self.recorder.get_recording_path("gemini", task_name)

        start_time = time.time()

        # Build Gemini CLI command
        cmd = ["gemini", "-p", prompt, "-o", "json", "--yolo"]

        # Prepare environment
        env = os.environ.copy()
        if self.api_key:
            env["GEMINI_API_KEY"] = self.api_key

        # Set cwd for subprocess (don't use os.chdir)
        cwd = self.task_dir if self.task_dir else None

        try:
            # Execute with asciinema recording if available
            if self.recorder.check_asciinema_available():
                result = subprocess.run(
                    ["asciinema", "rec", "-c", " ".join(cmd), recording_path],
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    env=env,
                    cwd=cwd,
                )
            else:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    env=env,
                    cwd=cwd,
                )
                recording_path = ""

            wall_time = time.time() - start_time
            stdout = result.stdout
            stderr = result.stderr
            success = result.returncode == 0

            # Parse metrics from JSON output
            metrics = self.parser.extract_metrics(stdout, stderr)

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
                token_count=metrics["tokens"],
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
        """Clean up Gemini process"""
        if self.process:
            self.process.terminate()
            self.process.wait(timeout=5)

    @staticmethod
    def check_available() -> bool:
        """Check if Gemini CLI is installed and available

        Returns:
            True if gemini is available, False otherwise
        """
        try:
            result = subprocess.run(
                ["gemini", "--version"],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False
