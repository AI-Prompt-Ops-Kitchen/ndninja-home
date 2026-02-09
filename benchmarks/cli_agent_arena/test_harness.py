"""Test harness for running and analyzing pytest results"""

import subprocess
import re
from dataclasses import dataclass
from typing import Optional


@dataclass
class HarnessResult:
    """Results from running tests"""
    passed: int
    failed: int
    total: int
    pass_rate: float
    output: str
    exit_code: int
    error: Optional[str] = None


class TestHarness:
    """Harness for running pytest and extracting metrics"""

    def run_tests(self, task_dir: str, test_command: str, timeout: int = 60) -> HarnessResult:
        """Run tests and extract results

        Args:
            task_dir: Directory containing test files
            test_command: Command to run (e.g., "pytest test_file.py -v")
            timeout: Maximum execution time in seconds

        Returns:
            TestResult with pass/fail counts and metrics
        """
        try:
            result = subprocess.run(
                test_command.split(),
                cwd=task_dir,
                capture_output=True,
                text=True,
                timeout=timeout
            )

            output = result.stdout + result.stderr

            # Parse pytest output for results
            # Look for patterns like "2 passed" or "1 failed, 1 passed"
            passed = 0
            failed = 0

            # Match "N passed" pattern
            passed_match = re.search(r'(\d+) passed', output)
            if passed_match:
                passed = int(passed_match.group(1))

            # Match "N failed" pattern
            failed_match = re.search(r'(\d+) failed', output)
            if failed_match:
                failed = int(failed_match.group(1))

            total = passed + failed
            pass_rate = (passed / total * 100.0) if total > 0 else 0.0

            return HarnessResult(
                passed=passed,
                failed=failed,
                total=total,
                pass_rate=pass_rate,
                output=output,
                exit_code=result.returncode
            )

        except subprocess.TimeoutExpired:
            return HarnessResult(
                passed=0,
                failed=0,
                total=0,
                pass_rate=0.0,
                output="",
                exit_code=-1,
                error=f"Test execution timed out after {timeout}s"
            )
        except Exception as e:
            return HarnessResult(
                passed=0,
                failed=0,
                total=0,
                pass_rate=0.0,
                output="",
                exit_code=-1,
                error=str(e)
            )
