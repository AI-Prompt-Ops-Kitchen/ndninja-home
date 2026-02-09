"""Gemini CLI output parser.

Parses JSON output from Gemini CLI (`gemini -o json`) to extract
token counts, costs, tool calls, retries, and error recovery.
"""

import json
from typing import Dict, Any
from .base_parser import BaseOutputParser


class GeminiParser(BaseOutputParser):
    """Parser for Gemini CLI JSON output format.

    Gemini CLI with `-o json` returns structured stats including
    model token usage, tool call counts, and error information.
    """

    # Google Gemini pricing (as of Feb 2026)
    # Gemini 2.0 Flash: ~$0.00025/1K input, ~$0.001/1K output
    INPUT_PRICE_PER_1K = 0.00025
    OUTPUT_PRICE_PER_1K = 0.001

    def extract_metrics(self, stdout: str, stderr: str) -> Dict[str, Any]:
        """Extract metrics from Gemini CLI JSON output.

        Args:
            stdout: Standard output from Gemini CLI (JSON format)
            stderr: Standard error from Gemini CLI

        Returns:
            Dictionary containing tokens, cost, retries, tool_calls,
            and error_recovered fields.
        """
        data = self._parse_json(stdout)

        tokens = self._extract_tokens(data)
        cost = self._calculate_cost(tokens)
        tool_calls = self._extract_tool_calls(data)
        retries = self._count_retries(data, stderr)
        error_recovered = self._detect_error_recovery(data)

        return {
            "tokens": tokens,
            "cost": cost,
            "retries": retries,
            "tool_calls": tool_calls,
            "error_recovered": error_recovered,
        }

    def _parse_json(self, stdout: str) -> dict:
        """Parse JSON from stdout, returning empty dict on failure."""
        try:
            return json.loads(stdout)
        except (json.JSONDecodeError, TypeError):
            return {}

    def _extract_tokens(self, data: dict) -> Dict[str, int]:
        """Extract token counts from Gemini stats.

        Sums across all models in stats.models[*].tokens.
        """
        tokens = {"input": 0, "output": 0}

        stats = data.get("stats", {})
        models = stats.get("models", [])

        for model in models:
            model_tokens = model.get("tokens", {})
            tokens["input"] += model_tokens.get("input", 0)
            tokens["output"] += model_tokens.get("output", 0)

        return tokens

    def _calculate_cost(self, tokens: Dict[str, int]) -> float:
        """Calculate cost from token counts using Gemini pricing."""
        input_cost = tokens["input"] * self.INPUT_PRICE_PER_1K / 1000
        output_cost = tokens["output"] * self.OUTPUT_PRICE_PER_1K / 1000
        return input_cost + output_cost

    def _extract_tool_calls(self, data: dict) -> int:
        """Extract total tool call count from stats.tools.totalCalls."""
        stats = data.get("stats", {})
        tools = stats.get("tools", {})
        return tools.get("totalCalls", 0)

    def _count_retries(self, data: dict, stderr: str) -> int:
        """Count retry attempts from data and stderr."""
        retries = 0

        # Check structured retry count
        stats = data.get("stats", {})
        retries += stats.get("retries", 0)

        # Also check stderr for retry patterns
        if stderr:
            import re
            retries += len(re.findall(r'retrying', stderr, re.IGNORECASE))

        return retries

    def _detect_error_recovery(self, data: dict) -> bool:
        """Detect if errors occurred but response was still produced."""
        has_error = "error" in data and data["error"] is not None
        has_response = "response" in data and data["response"] is not None
        return has_error and has_response
