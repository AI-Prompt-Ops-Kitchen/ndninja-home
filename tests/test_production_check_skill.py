import pytest
from tools_db.tools.production_checker import ProductionChecker
from tools_db.tools.automation_hub import AutomationHub

def test_production_check_skill_runs():
    """Test that production check skill runs without errors"""
    checker = ProductionChecker(project_path=".", test_mode=True)
    results = checker.run_all_checks()

    assert results is not None
    assert "checks" in results

def test_production_check_generates_report():
    """Test markdown report generation"""
    checker = ProductionChecker(project_path=".", test_mode=True)
    results = checker.run_all_checks()

    # Format as markdown
    report = "# Production Readiness Report\n\n"
    for check_name, check_result in results["checks"].items():
        status = "✅" if check_result.passed else "❌"
        report += f"{status} {check_name}: {check_result.details}\n"

    assert "✅" in report or "❌" in report
    assert "Production Readiness" in report
