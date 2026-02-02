"""Base adapter interface for CLI agents"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List


@dataclass
class BenchmarkResult:
    """Results from a single benchmark execution"""
    success: bool
    wall_time: float  # seconds
    token_count: Dict[str, int]  # {input: N, output: M}
    cost: float  # USD
    retries: int  # autonomy metric
    tool_calls: int  # autonomy metric
    error_recovered: bool  # autonomy metric
    generated_files: List[str]
    logs: str  # Full interaction log
    recording_path: str  # asciinema file path


class CLIAgentAdapter(ABC):
    """Abstract base class for CLI agent adapters"""

    @abstractmethod
    def setup(self, task_dir: str) -> None:
        """Prepare agent environment (cwd, context)

        Args:
            task_dir: Path to task directory containing prompt.md, tests/, etc.
        """
        pass

    @abstractmethod
    def execute_task(self, prompt: str, timeout: int) -> BenchmarkResult:
        """Run task and return metrics

        Args:
            prompt: Task description from prompt.md
            timeout: Maximum execution time in seconds

        Returns:
            BenchmarkResult with all metrics populated
        """
        pass

    @abstractmethod
    def cleanup(self) -> None:
        """Clean up agent process and resources"""
        pass
