#!/usr/bin/env python3
"""CLI Agent Benchmark Runner

Runs benchmark tasks against CLI coding agents (Kimi, Claude, Gemini)
and records metrics (speed, correctness, cost, autonomy, quality).
"""

import argparse
import sys
import uuid
from pathlib import Path
from typing import List

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from benchmarks.cli_agent_arena.task_loader import load_task, list_all_tasks
from benchmarks.cli_agent_arena.adapter_factory import get_adapter, check_adapter_availability


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
        choices=["mock", "kimi", "claude", "gemini"],
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

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run benchmarks without saving to database"
    )

    args = parser.parse_args()

    # Handle --list-tasks
    if args.list_tasks:
        print("Available benchmark tasks:\n")
        for task_path in list_tasks():
            task = load_task(f"benchmarks/shared-tasks/{task_path}")
            print(f"  {task_path:30s} ({task.difficulty:6s}, ~{task.estimated_time_seconds}s)")
        return 0

    # Handle execution
    if args.all or args.tasks or args.category:
        return run_benchmarks(args)

    print("No action specified. Use --help for usage information.")
    return 1


def run_benchmarks(args):
    """Run benchmarks based on arguments

    Args:
        args: Parsed command-line arguments

    Returns:
        Exit code (0 = success)
    """
    # Determine which tasks to run
    if args.all or args.category:
        all_tasks = list_tasks()
        if args.category:
            task_list = [t for t in all_tasks if t.startswith(f"{args.category}/")]
        else:
            task_list = all_tasks
    else:
        task_list = args.tasks or []

    if not task_list:
        print("No tasks to run")
        return 1

    # Determine which agents to test
    if args.all:
        agents = ["mock", "kimi", "claude", "gemini"]
    elif args.agent:
        agents = [args.agent]
    else:
        print("Error: Must specify --agent or --all")
        return 1

    # Check adapter availability
    availability = check_adapter_availability()

    run_id = str(uuid.uuid4())
    print(f"Benchmark Run ID: {run_id}\n")

    results = []
    for agent in agents:
        if not availability.get(agent, False):
            print(f"⚠️  Skipping {agent}: CLI not available")
            continue

        print(f"Running benchmarks with {agent}:")

        adapter = None
        for task_path in task_list:
            task = load_task(f"benchmarks/shared-tasks/{task_path}")
            print(f"  - {task.name} ({task.difficulty}, ~{task.estimated_time_seconds}s)...", end=" ", flush=True)

            try:
                # Get adapter
                adapter = get_adapter(agent)

                # Setup
                adapter.setup(str(task.task_dir))

                # Execute (this will fail for non-mock adapters)
                result = adapter.execute_task(task.prompt, timeout=task.estimated_time_seconds * 2)

                if result.success:
                    print(f"✅ Success ({result.wall_time:.1f}s)")
                else:
                    print(f"❌ Failed")

                results.append((agent, task, result))

            except NotImplementedError as e:
                print(f"⚠️  Not implemented: {e}")
            except Exception as e:
                print(f"❌ Error: {e}")
            finally:
                if adapter:
                    adapter.cleanup()

    # Summary
    print(f"\n{'='*60}")
    print(f"Completed {len(results)} benchmarks")

    if args.dry_run:
        print("(Dry run - results not saved to database)")
    else:
        # TODO: Save to database
        print("(Database saving not yet implemented)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
