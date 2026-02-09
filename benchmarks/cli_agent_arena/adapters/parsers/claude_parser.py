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

    def extract_metrics(self, stdout: str, stderr: str) -> Dict[str, Any]:
        """Extract all metrics from Claude output

        Args:
            stdout: Standard output from Claude CLI
            stderr: Standard error from Claude CLI

        Returns:
            Dictionary with all extracted metrics
        """
        output = stdout + "\n" + stderr

        # Extract tokens
        tokens = self.extract_tokens(output)

        return {
            "token_count": tokens,
            "cost": 0.0,  # Calculated separately
            "tool_calls": 0,  # Implemented in next task
            "retries": 0,  # Implemented in next task
            "error_recovered": False,  # Implemented in next task
        }
