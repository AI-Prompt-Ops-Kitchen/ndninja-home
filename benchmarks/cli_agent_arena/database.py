"""Database persistence layer for benchmark results"""

import psycopg2
from psycopg2.extras import RealDictCursor
from typing import List, Dict, Any, Optional
from adapters.base import BenchmarkResult
from test_harness import TestResult
from scoring import Score


class DatabaseClient:
    """Client for saving and retrieving benchmark results"""

    def __init__(
        self,
        host: str = "localhost",
        database: str = "workspace",
        user: str = "ndninja",
        password: str = None
    ):
        """Initialize database client

        Args:
            host: Database host
            database: Database name
            user: Database user
            password: Database password (optional)
        """
        self.host = host
        self.database = database
        self.user = user
        self.password = password

    def _get_connection(self):
        """Get database connection"""
        conn_params = {
            "database": self.database,
            "user": self.user
        }
        # Only add host if explicitly set and not localhost (to allow Unix socket)
        if self.host and self.host != "localhost":
            conn_params["host"] = self.host
        if self.password is not None:
            conn_params["password"] = self.password
        return psycopg2.connect(**conn_params)

    def save_result(
        self,
        agent_name: str,
        task_name: str,
        task_category: str,
        benchmark_result: BenchmarkResult,
        test_result: TestResult,
        score: Score
    ) -> int:
        """Save benchmark result to database

        Args:
            agent_name: Name of agent (kimi, claude, gemini)
            task_name: Name of task (quicksort, etc.)
            task_category: Task category (algorithms, etc.)
            benchmark_result: Benchmark execution results
            test_result: Test execution results
            score: Calculated scores

        Returns:
            Result ID from database
        """
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO cli_agent_benchmark_results (
                        agent_name,
                        task_name,
                        task_category,
                        wall_time_seconds,
                        token_count_input,
                        token_count_output,
                        actual_cost_usd,
                        retries,
                        tool_calls,
                        error_recovered,
                        tests_passed,
                        tests_failed,
                        tests_total,
                        speed_score,
                        correctness_score,
                        cost_score,
                        autonomy_score,
                        code_quality_score,
                        overall_score,
                        recording_path,
                        interaction_log
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                        %s
                    ) RETURNING id
                """, (
                    agent_name,
                    task_name,
                    task_category,
                    benchmark_result.wall_time,
                    benchmark_result.token_count.get("input", 0),
                    benchmark_result.token_count.get("output", 0),
                    benchmark_result.cost,
                    benchmark_result.retries,
                    benchmark_result.tool_calls,
                    benchmark_result.error_recovered,
                    test_result.passed,
                    test_result.failed,
                    test_result.total,
                    score.speed_score,
                    score.correctness_score,
                    score.cost_score,
                    score.autonomy_score,
                    score.quality_score,
                    score.total_score,
                    benchmark_result.recording_path,
                    benchmark_result.logs
                ))
                result_id = cur.fetchone()[0]
                conn.commit()
                return result_id
        finally:
            conn.close()

    def get_recent_results(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent benchmark results

        Args:
            limit: Maximum number of results to return

        Returns:
            List of result dictionaries
        """
        conn = self._get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT *
                    FROM cli_agent_benchmark_results
                    ORDER BY timestamp DESC
                    LIMIT %s
                """, (limit,))
                return [dict(row) for row in cur.fetchall()]
        finally:
            conn.close()

    def get_agent_comparison(self) -> List[Dict[str, Any]]:
        """Get agent comparison from view

        Returns:
            List of agent comparison dictionaries
        """
        conn = self._get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT * FROM cli_agent_comparison")
                return [dict(row) for row in cur.fetchall()]
        finally:
            conn.close()
