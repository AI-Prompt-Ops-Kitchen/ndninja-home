#!/usr/bin/env python3
"""
Docker Environment Debugger

Diagnoses Python environment issues in Docker containers.
"""

import subprocess
import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass


@dataclass
class EnvironmentCheck:
    check_name: str
    passed: bool
    result: str
    details: Optional[Dict[str, Any]] = None


class DockerDebugger:
    """Diagnose Docker container Python environment"""

    def __init__(self, container_id: Optional[str] = None):
        self.container_id = container_id

    def get_available_checks(self) -> List[str]:
        """List all available checks"""
        return [
            "python_version",
            "python_path",
            "installed_packages",
            "environment_variables",
            "pip_config",
            "sys_path",
            "venv_status"
        ]

    def run_command(self, command: str, use_container: bool = True) -> Dict[str, Any]:
        """Run command in container or locally"""
        try:
            if use_container and self.container_id:
                full_cmd = ["docker", "exec", self.container_id] + command.split()
            else:
                full_cmd = command.split()

            result = subprocess.run(
                full_cmd,
                capture_output=True,
                text=True,
                timeout=10
            )

            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Command timeout",
                "stdout": "",
                "stderr": "Command execution timeout"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "stdout": "",
                "stderr": str(e)
            }

    def check_python_version(self) -> EnvironmentCheck:
        """Check Python version in container"""
        result = self.run_command("python3 --version")

        if result["success"]:
            version = result["stdout"].strip()
            return EnvironmentCheck(
                check_name="python_version",
                passed=True,
                result=version,
                details={"version": version}
            )
        else:
            return EnvironmentCheck(
                check_name="python_version",
                passed=False,
                result="Python not found or not working",
                details={"error": result.get("stderr", "")}
            )

    def check_python_path(self) -> EnvironmentCheck:
        """Check Python executable path"""
        result = self.run_command("which python3")

        if result["success"]:
            path = result["stdout"].strip()
            return EnvironmentCheck(
                check_name="python_path",
                passed=True,
                result=path,
                details={"path": path}
            )
        else:
            return EnvironmentCheck(
                check_name="python_path",
                passed=False,
                result="Python path not found",
                details={"error": result.get("stderr", "")}
            )

    def check_installed_packages(self) -> EnvironmentCheck:
        """Check installed Python packages"""
        result = self.run_command("pip list --format json")

        if result["success"]:
            try:
                packages = json.loads(result["stdout"])
                return EnvironmentCheck(
                    check_name="installed_packages",
                    passed=True,
                    result=f"{len(packages)} packages installed",
                    details={"package_count": len(packages), "packages": packages}
                )
            except json.JSONDecodeError:
                return EnvironmentCheck(
                    check_name="installed_packages",
                    passed=False,
                    result="Failed to parse pip output",
                    details={"raw_output": result["stdout"]}
                )
        else:
            return EnvironmentCheck(
                check_name="installed_packages",
                passed=False,
                result="pip list failed",
                details={"error": result.get("stderr", "")}
            )

    def check_environment_variables(self) -> EnvironmentCheck:
        """Check Python-related environment variables"""
        result = self.run_command("env | grep -E 'PYTHON|PATH|VIRTUAL'")

        env_vars = {}
        if result["success"]:
            for line in result["stdout"].strip().split('\n'):
                if '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key] = value

        return EnvironmentCheck(
            check_name="environment_variables",
            passed=len(env_vars) > 0,
            result=f"Found {len(env_vars)} Python-related variables",
            details={"variables": env_vars}
        )

    def check_sys_path(self) -> EnvironmentCheck:
        """Check Python sys.path"""
        cmd = 'python3 -c "import sys; print(json.dumps(sys.path))" 2>/dev/null || echo "{}"'
        result = self.run_command(cmd)

        if result["success"]:
            try:
                paths = json.loads(result["stdout"].strip())
                return EnvironmentCheck(
                    check_name="sys_path",
                    passed=len(paths) > 0,
                    result=f"{len(paths)} paths in sys.path",
                    details={"paths": paths}
                )
            except:
                return EnvironmentCheck(
                    check_name="sys_path",
                    passed=False,
                    result="Failed to parse sys.path",
                    details={}
                )
        else:
            return EnvironmentCheck(
                check_name="sys_path",
                passed=False,
                result="Failed to check sys.path",
                details={"error": result.get("stderr", "")}
            )

    def run_all_checks(self) -> Dict[str, Any]:
        """Run all diagnostic checks"""
        checks = [
            self.check_python_version(),
            self.check_python_path(),
            self.check_installed_packages(),
            self.check_environment_variables(),
            self.check_sys_path(),
        ]

        passed = sum(1 for c in checks if c.passed)

        return {
            "container_id": self.container_id,
            "total_checks": len(checks),
            "passed": passed,
            "failed": len(checks) - passed,
            "checks": [
                {
                    "name": c.check_name,
                    "passed": c.passed,
                    "result": c.result,
                    "details": c.details
                }
                for c in checks
            ],
            "summary": f"{passed}/{len(checks)} checks passed"
        }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Docker Environment Debugger")
    parser.add_argument(
        "container",
        nargs="?",
        help="Docker container ID or name (if not provided, runs locally)"
    )
    parser.add_argument(
        "--check",
        choices=[
            "python_version", "python_path", "installed_packages",
            "environment_variables", "sys_path", "all"
        ],
        default="all",
        help="Specific check to run"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON"
    )

    args = parser.parse_args()

    debugger = DockerDebugger(container_id=args.container)

    if args.check == "all":
        result = debugger.run_all_checks()
    else:
        method = getattr(debugger, f"check_{args.check}")
        check = method()
        result = {
            "check": check.check_name,
            "passed": check.passed,
            "result": check.result,
            "details": check.details
        }

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        if args.check == "all":
            print(f"Docker Environment Diagnostic Report")
            print(f"Container: {result['container_id'] or 'local'}")
            print(f"Summary: {result['summary']}")
            print("\nChecks:")
            for check in result["checks"]:
                status = "✓" if check["passed"] else "✗"
                print(f"  {status} {check['name']}: {check['result']}")
        else:
            check = result
            status = "✓" if check["passed"] else "✗"
            print(f"{status} {check['check']}: {check['result']}")
            if check["details"]:
                print(f"  Details: {json.dumps(check['details'], indent=2)}")
