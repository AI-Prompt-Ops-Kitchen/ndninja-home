"""Kimi CLI adapter"""

import subprocess
import time
import os
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from adapters.base import CLIAgentAdapter, BenchmarkResult
from recording_manager import RecordingManager
from adapters.parsers.kimi_parser import KimiParser
from quality.analyzer import QualityAnalyzer


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
        self.parser = KimiParser()
        self.quality_analyzer = QualityAnalyzer()
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
        """
        # Generate recording path
        task_name = Path(self.task_dir).name if self.task_dir else "unknown"
        recording_path = self.recorder.get_recording_path("kimi", task_name)

        # Track time
        start_time = time.time()

        # Build Kimi CLI command
        cmd = ["kimi"]
        if self.api_key:
            cmd.extend(["--api-key", self.api_key])

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
            metrics = self.parser.extract_metrics(stdout, stderr)

            # Find generated files
            generated_files = self._find_generated_files()

            # Analyze code quality
            quality_score = self.quality_analyzer.analyze(generated_files)

            # Build result
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
                logs=f"Timeout after {timeout}s",
                recording_path=recording_path,
                quality_score=0.0,
            )

        except FileNotFoundError:
            # Kimi CLI not installed
            raise RuntimeError(
                "Kimi CLI not found. Install with: pip install kimi-cli"
            )

    def cleanup(self) -> None:
        """Clean up Kimi CLI process"""
        if self.process:
            self.process.terminate()
            self.process.wait(timeout=5)

    def _find_generated_files(self) -> list:
        """Find Python files generated in task directory.

        Returns:
            List of absolute paths to generated .py files
        """
        if not self.task_dir:
            return []

        generated = []
        task_path = Path(self.task_dir)

        # Find all .py files (excluding test files for now)
        for py_file in task_path.glob("*.py"):
            if not py_file.name.startswith("test_"):
                generated.append(str(py_file.absolute()))

        return generated

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
