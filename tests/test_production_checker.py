import pytest
from pathlib import Path
from tools_db.tools.production_checker import ProductionChecker, CheckResult


def test_production_checker_init():
    """Test ProductionChecker initialization"""
    checker = ProductionChecker(project_path=".", test_mode=True)
    assert str(checker.project_path) == "."
    assert checker.test_mode is True

def test_production_checker_run_all_checks():
    """Test running all production checks"""
    checker = ProductionChecker(project_path=".", test_mode=True)
    results = checker.run_all_checks()

    assert results is not None
    assert "checks" in results
    assert isinstance(results["checks"], dict)
    # Should have keys for each check type
    assert "tests" in results["checks"] or "security" in results["checks"]

def test_production_checker_calculate_go_nogo():
    """Test go/no-go decision logic"""
    checker = ProductionChecker(project_path=".", test_mode=True)

    # All passing
    passing_results = {
        "tests": CheckResult("tests", True, "47/47 passing"),
        "security": CheckResult("security", True, "No issues"),
        "documentation": CheckResult("documentation", True, "5/5 present"),
    }
    decision = checker.calculate_decision(passing_results)
    assert decision in ["go", "warning"]

    # Some failing
    failing_results = {
        "tests": CheckResult("tests", False, "3/47 failing"),
        "security": CheckResult("security", True, "No issues"),
    }
    decision = checker.calculate_decision(failing_results)
    assert decision == "no_go"
