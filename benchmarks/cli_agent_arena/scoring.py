"""Scoring engine for calculating benchmark scores"""

from dataclasses import dataclass
from adapters.base import BenchmarkResult
from test_harness import TestResult


@dataclass
class Score:
    """Comprehensive score breakdown"""
    speed_score: float  # 25% weight
    correctness_score: float  # 40% weight
    cost_score: float  # 15% weight
    autonomy_score: float  # 12% weight
    quality_score: float  # 8% weight
    total_score: float  # Sum of all scores (max 100)


class ScoringEngine:
    """Calculate scores across 5 dimensions"""

    # Score weights
    SPEED_WEIGHT = 0.25
    CORRECTNESS_WEIGHT = 0.40
    COST_WEIGHT = 0.15
    AUTONOMY_WEIGHT = 0.12
    QUALITY_WEIGHT = 0.08

    def calculate_speed_score(self, actual_time: float, estimated_time: float) -> float:
        """Calculate speed score (0-25 points)

        Args:
            actual_time: Actual execution time in seconds
            estimated_time: Estimated time budget in seconds

        Returns:
            Speed score (0-25)
        """
        max_score = 25.0

        # Calculate ratio of actual to estimated
        ratio = actual_time / estimated_time

        # Perfect score if under half the time
        if ratio <= 0.5:
            return max_score

        # Linear penalty from 0.5x to 2x
        if ratio <= 2.0:
            return max_score * (1.0 - (ratio - 0.5) / 1.5)

        # Heavy penalty beyond 2x
        return max(0.0, max_score * 0.1 / ratio)

    def calculate_correctness_score(self, test_result: TestResult) -> float:
        """Calculate correctness score (0-40 points)

        Args:
            test_result: Test execution results

        Returns:
            Correctness score (0-40)
        """
        max_score = 40.0
        return max_score * (test_result.pass_rate / 100.0)

    def calculate_cost_score(self, actual_cost: float, budgeted_cost: float) -> float:
        """Calculate cost score (0-15 points)

        Args:
            actual_cost: Actual API cost in USD
            budgeted_cost: Budgeted cost in USD

        Returns:
            Cost score (0-15)
        """
        max_score = 15.0

        if budgeted_cost == 0:
            return max_score

        ratio = actual_cost / budgeted_cost

        # Perfect score if under budget
        if ratio <= 1.0:
            return max_score

        # Penalty for over budget
        return max(0.0, max_score / ratio)

    def calculate_autonomy_score(
        self,
        retries: int,
        error_recovered: bool,
        tool_calls: int
    ) -> float:
        """Calculate autonomy score (0-12 points)

        Args:
            retries: Number of retries
            error_recovered: Whether errors were recovered
            tool_calls: Number of tool calls

        Returns:
            Autonomy score (0-12)
        """
        max_score = 12.0
        score = max_score

        # Penalty for retries (1 point per retry, max 5)
        retry_penalty = min(retries, 5) * 1.0
        score -= retry_penalty

        # Bonus for error recovery
        if error_recovered:
            score += 2.0

        # Efficiency penalty for excessive tool calls (>15)
        if tool_calls > 15:
            efficiency_penalty = (tool_calls - 15) * 0.2
            score -= min(efficiency_penalty, 3.0)

        return max(0.0, min(score, max_score))

    def calculate_quality_score(self, linting_issues: int, file_count: int) -> float:
        """Calculate code quality score (0-8 points)

        Args:
            linting_issues: Number of linting issues
            file_count: Number of generated files

        Returns:
            Quality score (0-8)
        """
        max_score = 8.0

        if file_count == 0:
            return 0.0

        # Penalty per linting issue
        issues_per_file = linting_issues / file_count
        penalty = min(issues_per_file * 2.0, max_score)

        return max(0.0, max_score - penalty)

    def calculate_total_score(
        self,
        benchmark_result: BenchmarkResult,
        test_result: TestResult,
        estimated_time: float,
        budgeted_cost: float,
        linting_issues: int
    ) -> Score:
        """Calculate total score across all dimensions

        Args:
            benchmark_result: Benchmark execution results
            test_result: Test execution results
            estimated_time: Time budget in seconds
            budgeted_cost: Cost budget in USD
            linting_issues: Number of linting issues

        Returns:
            Score object with all dimensions
        """
        speed_score = self.calculate_speed_score(
            benchmark_result.wall_time,
            estimated_time
        )

        correctness_score = self.calculate_correctness_score(test_result)

        cost_score = self.calculate_cost_score(
            benchmark_result.cost,
            budgeted_cost
        )

        autonomy_score = self.calculate_autonomy_score(
            benchmark_result.retries,
            benchmark_result.error_recovered,
            benchmark_result.tool_calls
        )

        quality_score = self.calculate_quality_score(
            linting_issues,
            len(benchmark_result.generated_files)
        )

        total = (
            speed_score +
            correctness_score +
            cost_score +
            autonomy_score +
            quality_score
        )

        return Score(
            speed_score=speed_score,
            correctness_score=correctness_score,
            cost_score=cost_score,
            autonomy_score=autonomy_score,
            quality_score=quality_score,
            total_score=total
        )
