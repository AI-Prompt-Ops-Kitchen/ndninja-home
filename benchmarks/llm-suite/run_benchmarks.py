#!/usr/bin/env python3
"""
Multi-Dimensional LLM Benchmark Suite
Comprehensive evaluation of local LLMs across multiple dimensions.
"""

import argparse
import json
import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import yaml


@dataclass
class BenchmarkResult:
    """Result from a single benchmark"""
    benchmark_name: str
    category: str
    model: str
    generation_time: float
    correctness_score: float  # 0-100
    code_quality_score: float  # 0-100
    performance_score: float  # 0-100
    security_score: float  # 0-100
    overall_score: float  # Weighted average
    generated_code: str
    test_output: str
    validation_report: dict
    errors: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        return {
            "benchmark_name": self.benchmark_name,
            "category": self.category,
            "model": self.model,
            "generation_time": self.generation_time,
            "correctness_score": self.correctness_score,
            "code_quality_score": self.code_quality_score,
            "performance_score": self.performance_score,
            "security_score": self.security_score,
            "overall_score": self.overall_score,
            "generated_code": self.generated_code,
            "test_output": self.test_output,
            "validation_report": self.validation_report,
            "errors": self.errors,
            "timestamp": self.timestamp
        }


class LLMBenchmarkRunner:
    """Runs LLM benchmarks"""

    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = Path(config_path)
        self.config = self.load_config()
        self.results: List[BenchmarkResult] = []
        self.vengeance_host = self.config["vengeance"]["host"]
        self.vengeance_user = self.config["vengeance"]["user"]

    def load_config(self) -> dict:
        """Load configuration from YAML"""
        with open(self.config_path) as f:
            return yaml.safe_load(f)

    def get_benchmark_prompt(self, benchmark_path: Path) -> str:
        """Load benchmark prompt"""
        prompt_file = benchmark_path / "prompt.txt"
        if not prompt_file.exists():
            raise FileNotFoundError(f"Prompt not found: {prompt_file}")
        return prompt_file.read_text()

    def generate_code(self, model: str, prompt: str, timeout: int = 300) -> tuple[str, float]:
        """Generate code using Ollama on Vengeance"""
        print(f"  Generating code with {model}...", end=" ", flush=True)

        start_time = time.time()

        try:
            # SSH to Vengeance and run Ollama
            cmd = [
                "ssh",
                f"{self.vengeance_user}@{self.vengeance_host}",
                f'ollama run {model} "{prompt}"'
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=True
            )

            generation_time = time.time() - start_time
            code = result.stdout

            # Extract code from markdown if wrapped
            if "```" in code:
                lines = code.split('\n')
                in_code_block = False
                code_lines = []
                for line in lines:
                    if line.startswith('```'):
                        in_code_block = not in_code_block
                        continue
                    if in_code_block:
                        code_lines.append(line)
                code = '\n'.join(code_lines)

            print(f"✓ ({generation_time:.1f}s)")
            return code, generation_time

        except subprocess.TimeoutExpired:
            print(f"✗ (timeout)")
            raise
        except subprocess.CalledProcessError as e:
            print(f"✗ (error)")
            raise RuntimeError(f"Code generation failed: {e.stderr}")

    def validate_code(self, code: str, language: str = "python") -> dict:
        """Validate generated code"""
        print(f"  Validating code...", end=" ", flush=True)

        validator = Path(self.config["validation"]["pipeline"])

        try:
            result = subprocess.run(
                [str(validator), "--json", "-"],
                input=code,
                capture_output=True,
                text=True,
                timeout=60
            )

            report = json.loads(result.stdout)
            passed = report.get("passed", False)

            if passed:
                print("✓")
            else:
                error_count = report.get("error_count", 0)
                warning_count = report.get("warning_count", 0)
                print(f"⚠ ({error_count} errors, {warning_count} warnings)")

            return report

        except subprocess.TimeoutExpired:
            print("✗ (timeout)")
            return {"passed": False, "error": "validation timeout"}
        except Exception as e:
            print(f"✗ ({e})")
            return {"passed": False, "error": str(e)}

    def run_tests(self, benchmark_path: Path, code: str, timeout: int = 60) -> tuple[float, str]:
        """Run unit tests against generated code"""
        print(f"  Running tests...", end=" ", flush=True)

        # Save generated code to temp file
        code_file = benchmark_path / ".generated_code.py"
        code_file.write_text(code)

        try:
            # Find test file
            test_files = list(benchmark_path.glob("test_*.py"))
            if not test_files:
                print("⚠ (no tests found)")
                return 0.0, "No test file found"

            test_file = test_files[0]

            # Run pytest (use relative path since cwd is benchmark_path)
            result = subprocess.run(
                ["pytest", test_file.name, "-v", "--tb=short"],
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=str(benchmark_path)
            )

            # Parse pytest output to get pass rate
            output = result.stdout + result.stderr

            # Look for "X passed" in output
            import re
            passed_match = re.search(r'(\d+) passed', output)
            failed_match = re.search(r'(\d+) failed', output)

            passed = int(passed_match.group(1)) if passed_match else 0
            failed = int(failed_match.group(1)) if failed_match else 0
            total = passed + failed

            if total == 0:
                score = 0.0
                print("✗ (no tests ran)")
            else:
                score = (passed / total) * 100
                if score == 100:
                    print(f"✓ ({passed}/{total})")
                else:
                    print(f"⚠ ({passed}/{total})")

            return score, output

        except subprocess.TimeoutExpired:
            print("✗ (timeout)")
            return 0.0, "Test execution timeout"
        except Exception as e:
            print(f"✗ ({e})")
            return 0.0, str(e)
        finally:
            # Cleanup
            if code_file.exists():
                code_file.unlink()

    def calculate_scores(
        self,
        validation_report: dict,
        test_pass_rate: float,
        generation_time: float
    ) -> tuple[float, float, float, float, float]:
        """Calculate individual and overall scores"""

        # Correctness: Direct from test pass rate
        correctness = test_pass_rate

        # Code Quality: Based on validation results
        quality = 100.0
        if not validation_report.get("passed", False):
            quality -= validation_report.get("error_count", 0) * 10
            quality -= validation_report.get("warning_count", 0) * 2
        quality = max(0, min(100, quality))

        # Performance: Based on generation time (lower is better)
        # Normalize against qwen2.5:32b baseline (44s)
        baseline_time = 44.0
        if generation_time <= baseline_time:
            performance = 100.0
        else:
            # Logarithmic penalty for slower times
            performance = max(0, 100 - (generation_time - baseline_time) * 2)

        # Security: Based on bandit results in validation
        security = 100.0
        for result in validation_report.get("results", []):
            if result.get("validator") == "bandit":
                if result.get("level") == "error":
                    security = 0.0
                elif result.get("level") == "warning":
                    security = 70.0

        # Overall: Weighted average
        weights = self.config["scoring"]
        overall = (
            correctness * weights["correctness"] +
            quality * weights["code_quality"] +
            performance * weights["performance"] +
            security * weights["security"]
        )

        return correctness, quality, performance, security, overall

    def run_benchmark(
        self,
        benchmark_path: Path,
        model: str,
        category: str
    ) -> BenchmarkResult:
        """Run a single benchmark"""

        benchmark_name = benchmark_path.name
        print(f"\n[{category}/{benchmark_name}] Model: {model}")

        errors = []

        try:
            # Get prompt
            prompt = self.get_benchmark_prompt(benchmark_path)

            # Generate code
            code, gen_time = self.generate_code(model, prompt)

            # Validate code
            validation = self.validate_code(code)

            # Run tests
            test_score, test_output = self.run_tests(benchmark_path, code)

            # Calculate scores
            correctness, quality, performance, security, overall = self.calculate_scores(
                validation, test_score, gen_time
            )

            print(f"  Scores: Overall={overall:.1f} (C:{correctness:.0f} Q:{quality:.0f} P:{performance:.0f} S:{security:.0f})")

            return BenchmarkResult(
                benchmark_name=benchmark_name,
                category=category,
                model=model,
                generation_time=gen_time,
                correctness_score=correctness,
                code_quality_score=quality,
                performance_score=performance,
                security_score=security,
                overall_score=overall,
                generated_code=code,
                test_output=test_output,
                validation_report=validation,
                errors=errors
            )

        except Exception as e:
            errors.append(str(e))
            print(f"  ✗ Benchmark failed: {e}")

            return BenchmarkResult(
                benchmark_name=benchmark_name,
                category=category,
                model=model,
                generation_time=0,
                correctness_score=0,
                code_quality_score=0,
                performance_score=0,
                security_score=0,
                overall_score=0,
                generated_code="",
                test_output="",
                validation_report={},
                errors=errors
            )

    def run_category(self, category_name: str, model: str) -> List[BenchmarkResult]:
        """Run all benchmarks in a category"""

        category_config = self.config["categories"].get(category_name)
        if not category_config or not category_config.get("enabled"):
            print(f"Category '{category_name}' not enabled")
            return []

        category_path = Path(category_name)
        if not category_path.exists():
            print(f"Category directory not found: {category_path}")
            return []

        results = []
        benchmarks = category_config.get("benchmarks", [])

        print(f"\n{'='*70}")
        print(f"Category: {category_name.upper()}")
        print(f"Benchmarks: {len(benchmarks)}")
        print(f"{'='*70}")

        for benchmark_name in benchmarks:
            benchmark_path = category_path / benchmark_name
            if not benchmark_path.exists():
                print(f"Benchmark not found: {benchmark_path}")
                continue

            result = self.run_benchmark(benchmark_path, model, category_name)
            results.append(result)
            self.results.append(result)

        return results

    def save_results(self, output_format: str = "json"):
        """Save benchmark results"""

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = Path(self.config["reports"]["output_dir"]) / timestamp
        output_dir.mkdir(parents=True, exist_ok=True)

        # Save JSON
        if "json" in self.config["reports"]["formats"]:
            json_file = output_dir / "results.json"
            with open(json_file, 'w') as f:
                json.dump([r.to_dict() for r in self.results], f, indent=2)
            print(f"\n✓ Results saved to {json_file}")

        # Save summary
        summary_file = output_dir / "summary.txt"
        with open(summary_file, 'w') as f:
            f.write(self.generate_summary())
        print(f"✓ Summary saved to {summary_file}")

    def generate_summary(self) -> str:
        """Generate text summary of results"""

        lines = []
        lines.append("="*70)
        lines.append("LLM BENCHMARK RESULTS")
        lines.append("="*70)
        lines.append("")

        # Group by model
        by_model = {}
        for result in self.results:
            if result.model not in by_model:
                by_model[result.model] = []
            by_model[result.model].append(result)

        for model, results in by_model.items():
            lines.append(f"Model: {model}")
            lines.append("-"*70)

            # Calculate averages
            avg_overall = sum(r.overall_score for r in results) / len(results)
            avg_correctness = sum(r.correctness_score for r in results) / len(results)
            avg_quality = sum(r.code_quality_score for r in results) / len(results)
            avg_performance = sum(r.performance_score for r in results) / len(results)
            avg_security = sum(r.security_score for r in results) / len(results)
            avg_time = sum(r.generation_time for r in results) / len(results)

            lines.append(f"  Benchmarks: {len(results)}")
            lines.append(f"  Overall Score: {avg_overall:.1f}/100")
            lines.append(f"    - Correctness: {avg_correctness:.1f}/100")
            lines.append(f"    - Code Quality: {avg_quality:.1f}/100")
            lines.append(f"    - Performance: {avg_performance:.1f}/100")
            lines.append(f"    - Security: {avg_security:.1f}/100")
            lines.append(f"  Avg Generation Time: {avg_time:.1f}s")
            lines.append("")

        lines.append("="*70)

        return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Run LLM benchmarks")
    parser.add_argument("--model", help="Model to benchmark")
    parser.add_argument("--category", help="Category to run (or 'all')")
    parser.add_argument("--config", default="config.yaml", help="Config file")
    parser.add_argument("--report", choices=["json", "html", "markdown"], default="json")

    args = parser.parse_args()

    runner = LLMBenchmarkRunner(args.config)

    # Determine model
    model = args.model
    if not model:
        # Use recommended production model
        for m in runner.config["models"]["production"]:
            if m.get("recommended"):
                model = m["name"]
                break

    if not model:
        print("Error: No model specified and no recommended model found")
        return 1

    # Determine categories
    categories = []
    if args.category and args.category != "all":
        categories = [args.category]
    else:
        categories = [
            name for name, cfg in runner.config["categories"].items()
            if cfg.get("enabled", False)
        ]

    # Run benchmarks
    print(f"\nRunning benchmarks for model: {model}")
    print(f"Categories: {', '.join(categories)}")

    for category in categories:
        runner.run_category(category, model)

    # Save results
    runner.save_results(args.report)

    # Print summary
    print("\n" + runner.generate_summary())

    return 0


if __name__ == "__main__":
    sys.exit(main())
