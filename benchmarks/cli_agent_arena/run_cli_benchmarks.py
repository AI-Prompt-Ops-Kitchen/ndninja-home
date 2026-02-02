#!/usr/bin/env python3
"""CLI Agent Benchmark Runner

Runs benchmark tasks against CLI coding agents (Kimi, Claude, Gemini)
and records metrics (speed, correctness, cost, autonomy, quality).
"""

import argparse
import sys
from pathlib import Path
from typing import List

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from benchmarks.cli_agent_arena.task_loader import load_task, list_all_tasks


def list_tasks() -> List[str]:
    """List all available benchmark tasks"""
    tasks_dir = Path("benchmarks/shared-tasks/algorithms")
    task_paths = []

    if not tasks_dir.exists():
        return task_paths

    for task_dir in tasks_dir.iterdir():
        if task_dir.is_dir() and (task_dir / "task.yaml").exists():
            task_paths.append(f"algorithms/{task_dir.name}")

    return sorted(task_paths)


def main():
    parser = argparse.ArgumentParser(
        description="CLI Agent Benchmark Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run quicksort with Kimi CLI
  %(prog)s --agent kimi --tasks algorithms/quicksort

  # Run all algorithm tasks with Claude
  %(prog)s --agent claude --category algorithms

  # List available tasks
  %(prog)s --list-tasks
        """
    )

    parser.add_argument(
        "--agent",
        choices=["kimi", "claude", "gemini"],
        help="CLI agent to benchmark"
    )

    parser.add_argument(
        "--tasks",
        nargs="+",
        help="Specific tasks to run (e.g., algorithms/quicksort)"
    )

    parser.add_argument(
        "--category",
        help="Run all tasks in a category (e.g., algorithms)"
    )

    parser.add_argument(
        "--list-tasks",
        action="store_true",
        help="List all available benchmark tasks"
    )

    parser.add_argument(
        "--all",
        action="store_true",
        help="Run all tasks for all agents"
    )

    args = parser.parse_args()

    # Handle --list-tasks
    if args.list_tasks:
        print("Available benchmark tasks:\n")
        for task_path in list_tasks():
            task = load_task(f"benchmarks/shared-tasks/{task_path}")
            print(f"  {task_path:30s} ({task.difficulty:6s}, ~{task.estimated_time_seconds}s)")
        return 0

    # TODO: Implement actual benchmark execution
    print("Benchmark execution not yet implemented")
    print(f"Would run: agent={args.agent}, tasks={args.tasks}, category={args.category}, all={args.all}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
