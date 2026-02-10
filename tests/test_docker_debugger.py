import pytest
from tools.docker_env_debugger import DockerDebugger


def test_docker_debugger_checks_python():
    """Should check Python version in container"""
    debugger = DockerDebugger()

    # Mock test - just verify the check exists
    checks = debugger.get_available_checks()
    assert "python_version" in checks
    assert "python_path" in checks
    assert "installed_packages" in checks


def test_docker_debugger_detects_issues():
    """Should detect common Docker environment issues"""
    debugger = DockerDebugger()

    # Verify issue detection methods exist
    assert hasattr(debugger, "check_python_version")
    assert hasattr(debugger, "check_installed_packages")
    assert hasattr(debugger, "check_environment_variables")
