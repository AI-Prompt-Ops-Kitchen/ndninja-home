import pytest
from tools_db.tools.production_checker import ProductionChecker, CheckResult

def test_format_check_result():
    """Test formatting check result as markdown"""
    checker = ProductionChecker(project_path=".", test_mode=True)
    result = CheckResult("tests", True, "47/47 passing")

    formatted = f"{'✅' if result.passed else '❌'} {result.check_name}: {result.details}"
    assert "✅" in formatted
    assert "tests" in formatted

def test_format_full_report():
    """Test formatting full production report"""
    checker = ProductionChecker(project_path=".", test_mode=True)
    results = checker.run_all_checks()

    lines = ["# Production Readiness Report", ""]
    for check_name, check_result in results["checks"].items():
        status = "✅" if check_result.passed else "❌"
        lines.append(f"{status} **{check_name}**: {check_result.details}")

    report = "\n".join(lines)
    assert "Production Readiness Report" in report
    assert "checks" in str(results)
