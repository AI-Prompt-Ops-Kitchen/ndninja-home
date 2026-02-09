"""Claude Code output parser"""

import re
from typing import Dict, Any
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from adapters.parsers.base_parser import BaseOutputParser


class ClaudeParser(BaseOutputParser):
    """Parser for Claude Code CLI output"""

    def extract_tokens(self, output: str) -> Dict[str, int]:
        """Extract token counts from Claude output

        Args:
            output: Claude CLI stdout/stderr

        Returns:
            Dictionary with 'input' and 'output' token counts
        """
        tokens = {"input": 0, "output": 0}

        # Pattern: "Input tokens: 1,234"
        input_match = re.search(r'Input tokens?:\s*([0-9,]+)', output, re.IGNORECASE)
        if input_match:
            tokens["input"] = int(input_match.group(1).replace(',', ''))

        # Pattern: "Output tokens: 567"
        output_match = re.search(r'Output tokens?:\s*([0-9,]+)', output, re.IGNORECASE)
        if output_match:
            tokens["output"] = int(output_match.group(1).replace(',', ''))

        return tokens

    def calculate_cost(self, tokens: Dict[str, int]) -> float:
        """Calculate cost from token counts

        Args:
            tokens: Dictionary with 'input' and 'output' counts

        Returns:
            Cost in USD
        """
        # Anthropic pricing (as of Feb 2026)
        # Sonnet 4.5: $3/MTok input, $15/MTok output
        INPUT_PRICE_PER_1K = 0.003
        OUTPUT_PRICE_PER_1K = 0.015

        input_cost = tokens.get("input", 0) * INPUT_PRICE_PER_1K / 1000
        output_cost = tokens.get("output", 0) * OUTPUT_PRICE_PER_1K / 1000

        return input_cost + output_cost

    def count_tool_calls(self, output: str) -> int:
        """Count tool usage from output

        Args:
            output: Claude CLI output

        Returns:
            Number of tool calls
        """
        # Pattern matches: "Using tool: X" or "Tool use:" or "<tool_use>"
        pattern = r'Using tool:|Tool use:|<tool_use>'
        matches = re.findall(pattern, output, re.IGNORECASE)
        return len(matches)

    def detect_retries(self, output: str) -> int:
        """Detect retry attempts from output

        Args:
            output: Claude CLI output

        Returns:
            Number of retries
        """
        # Pattern matches: "Retry", "Attempting again", "Re-attempting"
        pattern = r'Retry|Attempting again|Re-attempting'
        matches = re.findall(pattern, output, re.IGNORECASE)
        return len(matches)

    def detect_error_recovery(self, output: str, exit_code: int) -> bool:
        """Detect if errors were recovered from

        Args:
            output: Claude CLI output
            exit_code: Process exit code

        Returns:
            True if errors present but final success
        """
        has_errors = bool(re.search(r'Error:|Failed:|Exception:', output, re.IGNORECASE))
        successful_exit = exit_code == 0

        return has_errors and successful_exit

    def extract_metrics(self, stdout: str, stderr: str, exit_code: int = 0) -> Dict[str, Any]:
        """Extract all metrics from Claude output

        Args:
            stdout: Standard output from Claude CLI
            stderr: Standard error from Claude CLI
            exit_code: Process exit code

        Returns:
            Dictionary with all extracted metrics
        """
        output = stdout + "\n" + stderr

        # Extract tokens
        tokens = self.extract_tokens(output)

        # Calculate cost
        cost = self.calculate_cost(tokens)

        # Count tool calls
        tool_calls = self.count_tool_calls(output)

        # Detect retries
        retries = self.detect_retries(output)

        # Detect error recovery
        error_recovered = self.detect_error_recovery(output, exit_code)

        return {
            "token_count": tokens,
            "cost": cost,
            "tool_calls": tool_calls,
            "retries": retries,
            "error_recovered": error_recovered,
        }
