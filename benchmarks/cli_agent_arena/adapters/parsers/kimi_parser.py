"""Parser for Kimi CLI output.

This module provides a concrete parser for extracting metrics from
Kimi CLI tool output, including token counts, costs, retries, tool calls,
and error recovery patterns.
"""

import re
from typing import Dict, Any
from .base_parser import BaseOutputParser


class KimiParser(BaseOutputParser):
    """Parser for Kimi CLI output format.

    Extracts metrics from Kimi's output including:
    - Token usage (input/output tokens)
    - Cost calculation based on Moonshot API pricing
    - Retry attempts
    - Tool call counts
    - Error recovery detection
    """

    # Moonshot API pricing: $0.01 per 1000 tokens
    COST_PER_1K_TOKENS = 0.01

    def extract_metrics(self, stdout: str, stderr: str) -> Dict[str, Any]:
        """Extract metrics from Kimi CLI output.

        Args:
            stdout: Standard output from Kimi CLI execution
            stderr: Standard error from Kimi CLI execution

        Returns:
            Dictionary containing:
                - tokens (Dict[str, int]): Token usage with 'input' and 'output' keys
                - cost (float): Cost in USD based on Moonshot pricing
                - retries (int): Number of retry attempts
                - tool_calls (int): Number of tool calls made
                - error_recovered (bool): Whether errors were recovered from
        """
        tokens = self._extract_tokens(stdout)
        cost = self._calculate_cost(tokens)
        retries = self._count_retries(stderr)
        tool_calls = self._count_tool_calls(stdout)
        error_recovered = self._detect_error_recovery(stdout)

        return {
            "tokens": tokens,
            "cost": cost,
            "retries": retries,
            "tool_calls": tool_calls,
            "error_recovered": error_recovered,
        }

    def _extract_tokens(self, stdout: str) -> Dict[str, int]:
        """Extract token counts from stdout.

        Looks for pattern: "input=150, output=320" anywhere in output

        Args:
            stdout: Standard output from Kimi CLI

        Returns:
            Dictionary with 'input' and 'output' token counts, or zeros if not found
        """
        # Pattern: "input=(\d+), output=(\d+)"
        pattern = r'input=(\d+),\s*output=(\d+)'
        match = re.search(pattern, stdout)

        if match:
            return {
                "input": int(match.group(1)),
                "output": int(match.group(2)),
            }

        # Fallback to zeros if pattern not found
        return {"input": 0, "output": 0}

    def _calculate_cost(self, tokens: Dict[str, int]) -> float:
        """Calculate cost based on token usage and Moonshot pricing.

        Args:
            tokens: Dictionary with 'input' and 'output' token counts

        Returns:
            Cost in USD
        """
        total_tokens = tokens["input"] + tokens["output"]
        return (total_tokens / 1000.0) * self.COST_PER_1K_TOKENS

    def _count_retries(self, stderr: str) -> int:
        """Count retry attempts in stderr.

        Looks for occurrences of the word "retrying" (case-insensitive).

        Args:
            stderr: Standard error from Kimi CLI

        Returns:
            Number of retry attempts
        """
        # Count occurrences of "retrying" (case-insensitive)
        pattern = r"retrying"
        matches = re.findall(pattern, stderr, re.IGNORECASE)
        return len(matches)

    def _count_tool_calls(self, stdout: str) -> int:
        """Count tool call occurrences in stdout.

        Looks for pattern: "Executing tool:"

        Args:
            stdout: Standard output from Kimi CLI

        Returns:
            Number of tool calls made
        """
        pattern = r"Executing tool:"
        matches = re.findall(pattern, stdout)
        return len(matches)

    def _detect_error_recovery(self, stdout: str) -> bool:
        """Detect if errors were recovered from.

        Checks if stdout contains both "Error:" and "Success:" patterns,
        indicating an error occurred but was subsequently recovered.

        Args:
            stdout: Standard output from Kimi CLI

        Returns:
            True if error recovery detected, False otherwise
        """
        has_error = re.search(r"Error:", stdout) is not None
        has_success = re.search(r"Success:", stdout) is not None

        return has_error and has_success
