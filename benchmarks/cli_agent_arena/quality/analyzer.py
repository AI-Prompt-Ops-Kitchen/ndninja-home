"""Code quality analyzer using pylint and flake8.

This module provides the QualityAnalyzer class for analyzing Python code quality
using pylint (70% weight) and flake8 (30% weight).
"""

import subprocess
import os
from typing import List


class QualityAnalyzer:
    """Analyzer for Python code quality using pylint and flake8.

    Combines scores from pylint (70% weight) and flake8 (30% weight)
    to produce a final quality score from 0-100.
    """

    # Weights for combining scores
    PYLINT_WEIGHT = 0.7
    FLAKE8_WEIGHT = 0.3

    def analyze(self, file_paths: List[str]) -> float:
        """Analyze code quality for given files.

        Args:
            file_paths: List of Python file paths to analyze

        Returns:
            Quality score from 0-100 (higher is better)
        """
        # Handle empty file list
        if not file_paths:
            return 100.0

        # Filter to only existing files
        existing_files = [f for f in file_paths if os.path.exists(f)]

        # If no valid files, return 0
        if not existing_files:
            return 0.0

        # Run pylint and flake8
        pylint_score = self._run_pylint(existing_files)
        flake8_score = self._run_flake8(existing_files)

        # Combine scores with weights
        final_score = (self.PYLINT_WEIGHT * pylint_score) + (self.FLAKE8_WEIGHT * flake8_score)

        # Ensure score is within 0-100 range
        return max(0.0, min(100.0, final_score))

    def _run_pylint(self, file_paths: List[str]) -> float:
        """Run pylint on files and extract score.

        Args:
            file_paths: List of Python files to analyze

        Returns:
            Pylint score from 0-100
        """
        try:
            # Run pylint with machine-readable output
            result = subprocess.run(
                ["pylint", "--score=yes", "--output-format=text"] + file_paths,
                capture_output=True,
                text=True,
                timeout=30,
            )

            # Parse score from output
            # Pylint outputs: "Your code has been rated at X.XX/10.00"
            output = result.stdout + result.stderr
            score = self._parse_pylint_score(output)

            return score

        except subprocess.TimeoutExpired:
            # Timeout means very slow/complex code
            return 50.0
        except FileNotFoundError:
            # pylint not installed, use basic heuristics
            return self._fallback_score(file_paths)
        except Exception:
            # Any other error, use fallback
            return self._fallback_score(file_paths)

    def _parse_pylint_score(self, output: str) -> float:
        """Parse pylint score from output.

        Args:
            output: Pylint stdout/stderr

        Returns:
            Score from 0-100 (pylint's /10 score converted to /100)
        """
        import re

        # Look for "rated at X.XX/10"
        pattern = r"rated at ([-\d.]+)/10"
        match = re.search(pattern, output)

        if match:
            pylint_score = float(match.group(1))
            # Convert from /10 to /100
            return max(0.0, min(100.0, pylint_score * 10))

        # If score not found, return neutral
        return 50.0

    def _run_flake8(self, file_paths: List[str]) -> float:
        """Run flake8 on files and calculate score.

        Args:
            file_paths: List of Python files to analyze

        Returns:
            Flake8 score from 0-100 (based on error count)
        """
        try:
            # Run flake8
            result = subprocess.run(
                ["flake8", "--count"] + file_paths,
                capture_output=True,
                text=True,
                timeout=30,
            )

            # Count violations
            violations = self._parse_flake8_violations(result.stdout + result.stderr)

            # Calculate score based on violations
            # 0 violations = 100 points
            # Each violation deducts points
            score = max(0.0, 100.0 - (violations * 2))

            return score

        except subprocess.TimeoutExpired:
            # Timeout means very slow/complex code
            return 50.0
        except FileNotFoundError:
            # flake8 not installed, use basic heuristics
            return self._fallback_score(file_paths)
        except Exception:
            # Any other error, use fallback
            return self._fallback_score(file_paths)

    def _parse_flake8_violations(self, output: str) -> int:
        """Parse flake8 violation count from output.

        Args:
            output: Flake8 stdout/stderr

        Returns:
            Number of violations found
        """
        import re

        # Count lines that look like violations (filename:line:col: code message)
        pattern = r"^[^:]+:\d+:\d+: [A-Z]\d+ "
        lines = output.split("\n")
        violations = sum(1 for line in lines if re.match(pattern, line))

        return violations

    def _fallback_score(self, file_paths: List[str]) -> float:
        """Calculate basic quality score when linters not available.

        Uses simple heuristics like line length, docstrings, etc.

        Args:
            file_paths: List of Python files to analyze

        Returns:
            Estimated quality score from 0-100
        """
        total_score = 0.0
        file_count = 0

        for path in file_paths:
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()

                score = 100.0

                # Deduct for code smell indicators
                if 'pass' in content and len(content) < 50:
                    score -= 20  # Stub functions
                if ';' in content:
                    score -= 15  # Multiple statements per line
                if not ('"""' in content or "'''" in content):
                    score -= 10  # No docstrings
                if 'import' in content.split('\n')[0]:
                    score -= 5  # Imports not at top

                # Check line lengths
                lines = content.split('\n')
                long_lines = sum(1 for line in lines if len(line) > 100)
                score -= min(20, long_lines * 2)

                total_score += max(0, score)
                file_count += 1

            except Exception:
                # If we can't read the file, score it as 0
                file_count += 1

        if file_count == 0:
            return 100.0

        return total_score / file_count
