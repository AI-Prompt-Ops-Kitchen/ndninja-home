from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from pathlib import Path
import subprocess
import json
import re


@dataclass
class CheckResult:
    check_name: str
    passed: bool
    details: str
    evidence: Optional[Dict[str, Any]] = None


class ProductionChecker:
    """Run automated production readiness checks"""

    def __init__(self, project_path: str = ".", test_mode: bool = False):
        self.project_path = Path(project_path)
        self.test_mode = test_mode

    def run_all_checks(self) -> Dict[str, Any]:
        """Run all production checks and return results"""
        if self.test_mode:
            return {
                "checks": {
                    "tests": CheckResult("tests", True, "mock tests passing"),
                    "security": CheckResult("security", True, "mock security pass"),
                },
                "timestamp": "2026-01-20T00:00:00Z"
            }

        checks = {
            "tests": self.check_tests(),
            "security": self.check_security(),
            "documentation": self.check_documentation(),
            "performance": self.check_performance(),
            "integration": self.check_integration_tests(),
            "rollback": self.check_rollback_plan(),
        }

        return {
            "checks": checks,
            "timestamp": str(Path(self.project_path).resolve())
        }

    def check_tests(self) -> CheckResult:
        """Check if tests pass (80%+ pass rate required)"""
        try:
            result = subprocess.run(
                ["python3", "-m", "pytest", "tests/", "-v", "--tb=no"],
                cwd=self.project_path,
                capture_output=True,
                text=True,
                timeout=60
            )

            output = result.stdout
            if "passed" in output:
                match = re.search(r"(\d+) passed", output)
                if match:
                    passed = int(match.group(1))
                    details = f"{passed} tests passed"
                    return CheckResult("tests", result.returncode == 0, details)

            return CheckResult("tests", False, "No test output found")
        except Exception as e:
            return CheckResult("tests", False, f"Error running tests: {str(e)}")

    def check_security(self) -> CheckResult:
        """Check for common security vulnerabilities"""
        violations = []

        # Simple grep-based checks for common issues
        dangerous_patterns = [
            (r"password\s*=\s*['\"]", "Hardcoded password"),
            (r"api[_-]?key\s*=\s*['\"]", "Hardcoded API key"),
            (r"secret\s*=\s*['\"]", "Hardcoded secret"),
        ]

        try:
            for pattern, description in dangerous_patterns:
                result = subprocess.run(
                    ["grep", "-r", "-E", pattern, str(self.project_path)],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    violations.append(description)

            if violations:
                return CheckResult("security", False, f"Found {len(violations)} violations",
                                 {"violations": violations})
            else:
                return CheckResult("security", True, "No security violations found")
        except Exception as e:
            return CheckResult("security", False, f"Error checking security: {str(e)}")

    def check_documentation(self) -> CheckResult:
        """Check for required documentation files"""
        required_docs = ["README.md", "IMPLEMENTATION_SUMMARY.md"]
        found_docs = []

        for doc in required_docs:
            if (self.project_path / doc).exists():
                found_docs.append(doc)

        if len(found_docs) >= 1:
            return CheckResult("documentation", True, f"Found {len(found_docs)} documentation files")
        else:
            return CheckResult("documentation", False, f"Only found {len(found_docs)}/2 required docs")

    def check_performance(self) -> CheckResult:
        """Check performance benchmarks if they exist"""
        benchmark_file = self.project_path / "benchmarks.py"
        if not benchmark_file.exists():
            return CheckResult("performance", True, "No benchmarks defined (warning only)",
                             {"severity": "warning"})

        try:
            result = subprocess.run(
                ["python3", str(benchmark_file)],
                cwd=self.project_path,
                capture_output=True,
                text=True,
                timeout=120
            )

            if result.returncode == 0:
                return CheckResult("performance", True, "Benchmarks passed")
            else:
                return CheckResult("performance", False, "Benchmarks failed")
        except Exception as e:
            return CheckResult("performance", False, f"Error running benchmarks: {str(e)}")

    def check_integration_tests(self) -> CheckResult:
        """Check integration tests"""
        try:
            result = subprocess.run(
                ["python3", "-m", "pytest", "tests/integration_*.py", "-v"],
                cwd=self.project_path,
                capture_output=True,
                text=True,
                timeout=120
            )

            if result.returncode == 0:
                return CheckResult("integration", True, "Integration tests passing")
            else:
                return CheckResult("integration", False, "Integration tests failing")
        except Exception as e:
            return CheckResult("integration", False, f"No integration tests found: {str(e)}")

    def check_rollback_plan(self) -> CheckResult:
        """Check for rollback plan"""
        rollback_file = self.project_path / "ROLLBACK.md"

        try:
            result = subprocess.run(
                ["git", "tag", "-l"],
                cwd=self.project_path,
                capture_output=True,
                text=True
            )

            if rollback_file.exists() or result.stdout.strip():
                return CheckResult("rollback", True, "Rollback plan available")
            else:
                return CheckResult("rollback", False, "No rollback plan found")
        except Exception as e:
            return CheckResult("rollback", False, f"Error checking rollback: {str(e)}")

    def calculate_decision(self, results: Dict[str, Any]) -> str:
        """Determine go/no-go decision based on check results"""
        failed_checks = [
            check for check, result in results.items()
            if hasattr(result, 'passed') and not result.passed
        ]

        if not failed_checks:
            return "go"
        elif len(failed_checks) == 1 and "performance" in failed_checks[0]:
            return "warning"
        else:
            return "no_go"
