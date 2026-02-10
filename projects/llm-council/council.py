#!/usr/bin/env python3
"""
LLM Council CLI — queries 4 models in parallel, writes result JSON.

Usage:
    python3 council.py "Your prompt here"
    python3 council.py "Your prompt" --timeout 90

Output: /tmp/council_result.json
    {"individual_responses": {"claude-sonnet-4-5": "...", "gpt-4o": "...", ...}}

Exit codes: 0=success, 1=error, 2=all models failed
"""

import argparse
import json
import sys
from pathlib import Path

# Add scripts dir to path for lib imports
sys.path.insert(0, str(Path.home() / "scripts"))

from lib.llm_council import run_council, council_result_to_daily_review_format

OUTPUT_PATH = Path("/tmp/council_result.json")


def main():
    parser = argparse.ArgumentParser(description="LLM Council — multi-model query")
    parser.add_argument("prompt", help="Prompt to send to all models")
    parser.add_argument("--timeout", type=float, default=120.0, help="Timeout in seconds")
    args = parser.parse_args()

    try:
        result = run_council(args.prompt, timeout=args.timeout)
    except Exception as e:
        print(f"Fatal error: {e}", file=sys.stderr)
        return 1

    if result.models_succeeded == 0:
        print("All models failed", file=sys.stderr)
        for r in result.responses:
            print(f"  {r.model}: {r.error}", file=sys.stderr)
        return 2

    fmt = council_result_to_daily_review_format(result)
    OUTPUT_PATH.write_text(json.dumps(fmt, indent=2))

    print(f"Council complete: {result.models_succeeded}/{len(result.responses)} models responded")
    print(f"Output: {OUTPUT_PATH}")
    for r in result.responses:
        status = "OK" if r.success else f"FAIL ({r.error})"
        latency = f"{r.latency:.1f}s" if r.success else "-"
        print(f"  {r.model}: {status} [{latency}]")

    return 0


if __name__ == "__main__":
    sys.exit(main())
